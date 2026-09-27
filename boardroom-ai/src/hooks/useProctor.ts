import { useCallback, useEffect, useRef, useState } from "react";

export type Violation = { type: string; detail: string; at: string };

type Options = {
  active: boolean;
  onViolation: (v: Violation) => void;
};

const COOLDOWN_MS = 6000;
const WASM = "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.22-rc.20250304/wasm";
const MODEL =
  "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task";

/**
 * Integrity monitor: camera gaze/face tracking plus browser signals
 * (tab switch, focus loss, fullscreen exit, split screen, extra monitors,
 * dev tools, copy/paste, screenshots, overlays, camera shutdown).
 */
export function useProctor({ active, onViolation }: Options) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const stream = useRef<MediaStream | null>(null);
  const lastFire = useRef(0);
  const cb = useRef(onViolation);
  cb.current = onViolation;
  const [camReady, setCamReady] = useState(false);
  const [trackerReady, setTrackerReady] = useState(false);
  const [status, setStatus] = useState<"ok" | "away" | "noface" | "multi">("ok");
  const [camError, setCamError] = useState<string | null>(null);

  const fire = useCallback((type: string, detail: string) => {
    const now = Date.now();
    if (now - lastFire.current < COOLDOWN_MS) return;
    lastFire.current = now;
    cb.current({ type, detail, at: new Date().toISOString() });
  }, []);

  const startCamera = useCallback(async () => {
    try {
      const s = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480, facingMode: "user" }, audio: false });
      stream.current = s;
      if (videoRef.current) {
        videoRef.current.srcObject = s;
        await videoRef.current.play().catch(() => undefined);
      }
      setCamReady(true);
      setCamError(null);
      return true;
    } catch {
      setCamError("Camera access is required to sit this interview. Allow the camera and try again.");
      return false;
    }
  }, []);

  // Attach stream when the video element mounts later.
  useEffect(() => {
    if (videoRef.current && stream.current && !videoRef.current.srcObject) {
      videoRef.current.srcObject = stream.current;
      void videoRef.current.play().catch(() => undefined);
    }
  });

  useEffect(() => () => stream.current?.getTracks().forEach((t) => t.stop()), []);

  /* ---------- Camera: face + gaze ---------- */
  useEffect(() => {
    if (!active || !camReady) return;
    let cancelled = false;
    let timer: ReturnType<typeof setInterval> | undefined;
    let awaySince = 0;
    let noFaceSince = 0;
    const sweeps: number[] = [];
    let lastH = 0;

    void (async () => {
      const vision = await import("@mediapipe/tasks-vision");
      const files = await vision.FilesetResolver.forVisionTasks(WASM);
      const landmarker = await vision.FaceLandmarker.createFromOptions(files, {
        baseOptions: { modelAssetPath: MODEL, delegate: "GPU" },
        runningMode: "VIDEO",
        numFaces: 2,
        outputFaceBlendshapes: true,
      });
      if (cancelled) return;
      setTrackerReady(true);
      timer = setInterval(() => {
        const v = videoRef.current;
        if (!v || v.readyState < 2) return;
        const now = performance.now();
        const res = landmarker.detectForVideo(v, now);
        const faces = res.faceLandmarks.length;
        if (faces === 0) {
          setStatus("noface");
          noFaceSince ||= now;
          if (now - noFaceSince > 3000) fire("face_missing", "Candidate's face left the camera frame");
          return;
        }
        noFaceSince = 0;
        if (faces > 1) {
          setStatus("multi");
          fire("multiple_faces", "Another person was detected in the camera frame");
          return;
        }
        const shapes = res.faceBlendshapes[0]?.categories ?? [];
        const s = (n: string) => shapes.find((c) => c.categoryName === n)?.score ?? 0;
        // Horizontal gaze: + = looking to candidate's right
        const h = (s("eyeLookOutLeft") + s("eyeLookInRight") - s("eyeLookInLeft") - s("eyeLookOutRight")) / 2;
        const down = (s("eyeLookDownLeft") + s("eyeLookDownRight")) / 2;
        const up = (s("eyeLookUpLeft") + s("eyeLookUpRight")) / 2;
        // Head yaw from nose vs. face edges
        const lm = res.faceLandmarks[0]!;
        const nose = lm[1]!, left = lm[234]!, right = lm[454]!;
        const yaw = (nose.x - left.x) / Math.max(0.0001, right.x - left.x) - 0.5;
        const away = Math.abs(h) > 0.5 || up > 0.6 || down > 0.75 || Math.abs(yaw) > 0.22;
        if (away) {
          setStatus("away");
          awaySince ||= now;
          if (now - awaySince > 2500) fire("gaze_away", "Eyes or head turned away from the screen");
        } else {
          setStatus("ok");
          awaySince = 0;
        }
        // Teleprompter / off-screen reading: repeated steady left→right sweeps
        if (lastH < -0.25 && h > 0.25) sweeps.push(now);
        lastH = h;
        while (sweeps.length && now - sweeps[0]! > 12000) sweeps.shift();
        if (sweeps.length >= 7) {
          sweeps.length = 0;
          fire("reading_pattern", "Line-by-line reading eye pattern detected (possible teleprompter or hidden notes)");
        }
      }, 200);
    })().catch(() => setTrackerReady(false));

    const track = stream.current?.getVideoTracks()[0];
    const onEnded = () => fire("camera_off", "Camera was turned off or disconnected");
    track?.addEventListener("ended", onEnded);
    return () => {
      cancelled = true;
      if (timer) clearInterval(timer);
      track?.removeEventListener("ended", onEnded);
    };
  }, [active, camReady, fire]);

  /* ---------- Browser integrity signals ---------- */
  useEffect(() => {
    if (!active) return;
    const baseW = window.innerWidth;
    const onVis = () => document.hidden && fire("tab_switch", "Switched to another tab or minimised the window");
    const onBlur = () => fire("focus_lost", "Interview window lost focus (another app, overlay or AI assistant)");
    const onFs = () => !document.fullscreenElement && fire("fullscreen_exit", "Exited secure full-screen mode");
    const onResize = () => {
      if (window.innerWidth < baseW * 0.8) fire("split_screen", "Window was resized or split-screened");
      if (window.outerWidth - window.innerWidth > 200 || window.outerHeight - window.innerHeight > 250)
        fire("devtools", "Developer tools or a side panel was opened");
    };
    const block = (e: Event) => {
      e.preventDefault();
      fire("clipboard", "Copy, cut or paste attempted");
    };
    const onKey = (e: KeyboardEvent) => {
      const k = e.key.toLowerCase();
      if (k === "printscreen") fire("screenshot", "Screenshot key pressed");
      if (k === "f12" || ((e.ctrlKey || e.metaKey) && e.shiftKey && ["i", "j", "c"].includes(k))) {
        e.preventDefault();
        fire("devtools", "Developer tools shortcut used");
      }
      if ((e.ctrlKey || e.metaKey) && ["t", "n", "w", "p", "s", "f"].includes(k)) e.preventDefault();
    };
    const onCtx = (e: Event) => e.preventDefault();
    document.addEventListener("visibilitychange", onVis);
    window.addEventListener("blur", onBlur);
    document.addEventListener("fullscreenchange", onFs);
    window.addEventListener("resize", onResize);
    document.addEventListener("copy", block);
    document.addEventListener("cut", block);
    document.addEventListener("paste", block);
    document.addEventListener("keydown", onKey);
    document.addEventListener("contextmenu", onCtx);
    const scr = window.screen as Screen & { isExtended?: boolean };
    if (scr.isExtended) fire("extra_monitor", "A second display is connected");
    return () => {
      document.removeEventListener("visibilitychange", onVis);
      window.removeEventListener("blur", onBlur);
      document.removeEventListener("fullscreenchange", onFs);
      window.removeEventListener("resize", onResize);
      document.removeEventListener("copy", block);
      document.removeEventListener("cut", block);
      document.removeEventListener("paste", block);
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("contextmenu", onCtx);
    };
  }, [active, fire]);

  const stopAll = useCallback(() => {
    stream.current?.getTracks().forEach((t) => t.stop());
    if (document.fullscreenElement) void document.exitFullscreen().catch(() => undefined);
  }, []);

  return { videoRef, startCamera, camReady, trackerReady, status, camError, fire, stopAll };
}
