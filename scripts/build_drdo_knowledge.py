"""
Builds and updates the canonical seed_knowledge.json with:
1. Domain tags for existing software-engineering knowledge chunks ('cyber_computing').
2. 32 comprehensive, peer-reviewed, publicly referenced scientific and engineering knowledge chunks
   for the primary DRDO demonstration domain: 'electronics_radar' (Scientist 'B' ECE / Radar & Embedded).

Conforms strictly to PSWB01 Section 4, 6, 7, and 19.
Zero classified information; strictly standard academic and public aerospace/defence references.
"""

import json
from pathlib import Path


def generate_drdo_chunks():
    chunks = [
        # --- Stage 1: Ice Breaker ---
        {
            "id": "chunk_drdo_ice_01",
            "role_id": "scientist_b_ece",
            "competency": "ice_breaker",
            "stage": "ice_breaker",
            "difficulty_level": 1,
            "domain": "electronics_radar",
            "discipline": "Electronics & Communication Engineering",
            "topic": "Academic Background and Radar/Embedded Engineering Motivation",
            "title": "Candidate Background in Electronics, Signal Processing, and Embedded Systems",
            "content": "Ice-breaker context for Scientist 'B' (ECE / Radar & Embedded Systems) candidates. The interview board evaluates how clearly the candidate articulates their foundational background in electronics, signal processing, and real-time embedded systems, their academic projects, and their motivation for scientific research in defence technologies.",
            "expected_concepts": ["academic specialization", "project overview", "core engineering strengths", "research motivation"],
            "sample_questions": [
                "Could you walk the board through your academic background in Electronics & Communication and summarize your primary research or project focus?",
                "What motivated you to specialize in real-time embedded systems and signal processing, and how does your project work relate to radar systems?",
                "Can you describe your role and key technical contributions to your final year or post-graduate engineering project?"
            ],
            "rubric": {
                "poor": "Fails to articulate academic background, cannot clearly explain personal engineering contributions, or shows vague understanding of electronics fundamentals.",
                "acceptable": "Coherently summarizes academic journey, mentions specific microcontrollers, DSP tools, or lab equipment used, and outlines project deliverables.",
                "excellent": "Demonstrates structured technical communication, crisp explanation of design challenges overcome in hardware/software, and authentic enthusiasm for scientific research."
            },
            "source": "DRDO-RAC-Public-Interview-Structure",
            "source_title": "RAC Scientist 'B' Interview Assessment Framework",
            "source_type": "official_public",
            "source_reference": "RAC Public Guidelines / ECE Syllabus"
        },
        {
            "id": "chunk_drdo_ice_02",
            "role_id": "scientist_b_ece",
            "competency": "ice_breaker",
            "stage": "ice_breaker",
            "difficulty_level": 1,
            "domain": "electronics_radar",
            "discipline": "Electronics & Communication Engineering",
            "topic": "Laboratory Tooling and Hardware Debugging Experience",
            "title": "Practical Experience with Electronic Instrumentation and Development Toolchains",
            "content": "Warm-up assessment probing candidate familiarity with practical electronics laboratory tools: digital storage oscilloscopes (DSO), logic analyzers, spectrum analyzers, JTAG/SWD debuggers, and simulation suites like MATLAB/Simulink or Vivado.",
            "expected_concepts": ["oscilloscope measurements", "logic analyzer", "debugging toolchains", "simulation tools"],
            "sample_questions": [
                "What laboratory instruments or simulation environments have you used most extensively for debugging embedded hardware and signal waveforms?",
                "When an embedded microcontroller fails to communicate over an SPI or I2C bus, what diagnostic steps and tools do you use to locate the fault?",
                "How do you validate an algorithm in MATLAB or Simulink before porting it to embedded C on a target processor?"
            ],
            "rubric": {
                "poor": "Unfamiliar with standard lab instruments like DSOs or logic analyzers; cannot describe basic hardware debugging workflows.",
                "acceptable": "Identifies common tools (DSO, logic analyzer, MATLAB) and describes basic probing and signal validation steps.",
                "excellent": "Provides detailed hands-on debugging examples (e.g. trigger setups on DSOs, protocol decode on logic analyzers, simulation-to-silicon cross-verification)."
            },
            "source": "DRDO-RAC-Public-Interview-Structure",
            "source_title": "RAC Electronics Engineering Laboratory Assessment",
            "source_type": "official_public",
            "source_reference": "RAC ECE Practical Assessment Standards"
        },

        # --- Stage 2: Expertise Validation ---
        {
            "id": "chunk_drdo_val_01",
            "role_id": "scientist_b_ece",
            "competency": "embedded_realtime_systems",
            "stage": "expertise_validation",
            "difficulty_level": 2,
            "domain": "electronics_radar",
            "discipline": "Electronics & Communication Engineering",
            "topic": "Claim Validation: RTOS Task Scheduling and Inter-Task Synchronization",
            "title": "Verification of Claimed Embedded RTOS and Firmware Development Expertise",
            "content": "Probes candidate claims of hands-on embedded RTOS experience (e.g., FreeRTOS, Zephyr). Evaluates whether the candidate genuinely understands task priority management, tick interrupts, semaphore vs mutex differences, and how context switches are executed at the hardware register level on ARM Cortex-M architecture.",
            "expected_concepts": ["RTOS Priority Preemption", "mutex synchronization", "context switch", "task stacks"],
            "sample_questions": [
                "You claimed experience with real-time operating systems in your profile. How does a preemptive RTOS handle task switching during a timer tick interrupt?",
                "In FreeRTOS or a similar RTOS, what is the precise functional difference between a binary semaphore and a mutex, particularly regarding priority inheritance?",
                "How do you determine stack size allocation for independent concurrent tasks in an embedded application?"
            ],
            "rubric": {
                "poor": "Cannot explain how a preemptive context switch works; confuses binary semaphore with mutex; shows superficial resume claims.",
                "acceptable": "Explains that the highest priority ready task is scheduled; distinguishes mutex ownership from signaling semaphore.",
                "excellent": "Details ARM Cortex-M PendSV exception handling for context switching, explains TCB stack pointers, and demonstrates priority inheritance to prevent deadlock."
            },
            "source": "Laplante-Real-Time-Systems",
            "source_title": "Real-Time Systems Design and Analysis (Phillip A. Laplante)",
            "source_type": "textbook",
            "source_reference": "Laplante, 4th Ed., Chapter 3: Scheduling and Synchronization"
        },
        {
            "id": "chunk_drdo_val_02",
            "role_id": "scientist_b_ece",
            "competency": "digital_signal_processing",
            "stage": "expertise_validation",
            "difficulty_level": 2,
            "domain": "electronics_radar",
            "discipline": "Electronics & Communication Engineering",
            "topic": "Claim Validation: Digital Filter Implementation and Convolution",
            "title": "Verification of Claimed Digital Signal Processing and Filter Design Skills",
            "content": "Validates candidate claims regarding digital signal processing and filter design. Evaluates practical understanding of discrete convolution, difference equations, impulse response length, and the trade-offs between computational latency and transition band steepness.",
            "expected_concepts": ["FIR vs IIR Digital Filters", "discrete convolution", "impulse response", "filter coefficients"],
            "sample_questions": [
                "Your resume highlights DSP filter implementation. Can you write down the difference equation for a simple discrete-time filter and explain how convolution produces the output?",
                "Under what operational circumstances would you select an FIR filter over an IIR filter in a real-time radar receiver?",
                "How do you compute the computational complexity of an N-point FIR filter running at an Fs sampling rate?"
            ],
            "rubric": {
                "poor": "Cannot write a difference equation; confuses FIR with IIR; unaware of linear phase implications.",
                "acceptable": "Distinguishes finite vs infinite impulse response; identifies that FIR filters have guaranteed linear phase and stability.",
                "excellent": "Derives difference equations, analyzes phase distortion effects on radar pulses, and explains multiply-accumulate (MAC) throughput bottlenecks."
            },
            "source": "Proakis-Manolakis-DSP",
            "source_title": "Digital Signal Processing: Principles, Algorithms, and Applications",
            "source_type": "textbook",
            "source_reference": "Proakis & Manolakis, 4th Ed., Chapters 2 & 10"
        },

        # --- Stage 3: Fundamentals ---
        {
            "id": "chunk_drdo_fund_emb_01",
            "role_id": "scientist_b_ece",
            "competency": "embedded_realtime_systems",
            "stage": "fundamentals",
            "difficulty_level": 2,
            "domain": "electronics_radar",
            "discipline": "Electronics & Communication Engineering",
            "topic": "Interrupt Latency, Vector Tables, and ISR Design",
            "title": "Microcontroller Interrupt Latency and Interrupt Service Routine (ISR) Architecture",
            "content": "Interrupt latency is the time elapsed between an external hardware event asserting an interrupt request line and the execution of the first instruction in the corresponding Interrupt Service Routine (ISR). In modern microcontrollers (such as ARM Cortex-M Nested Vectored Interrupt Controller - NVIC), latency comprises pipeline flushing, hardware register state stacking (pushing R0-R3, R12, LR, PC, xPSR to stack), vector table address fetch, and ISR prologue execution. Key engineering design rules mandate that ISRs must be minimal, deterministic, and non-blocking, delegating heavy processing to deferred tasks via queues or semaphores.",
            "expected_concepts": ["Interrupt Latency & ISRs", "vector table", "hardware stacking", "deferred processing"],
            "sample_questions": [
                "What factors constitute interrupt latency in an embedded microcontroller, and how does the hardware save processor state?",
                "Why is it hazardous to execute blocking operations or dynamic memory allocation inside an Interrupt Service Routine?",
                "How does an NVIC prioritize simultaneous hardware interrupts when higher priority interrupts arrive during an ongoing ISR?"
            ],
            "rubric": {
                "poor": "Defines interrupt latency vaguely as 'delay'; unaware of hardware stacking or vector table lookups; suggests sleeping inside an ISR.",
                "acceptable": "Identifies that latency includes context saving and vector fetch; explains why ISRs must be fast and non-blocking.",
                "excellent": "Quantifies cycles for hardware context stacking/unstacking, describes tail-chaining in ARM NVIC, and explains bottom-half / deferred task architectures."
            },
            "source": "Yiu-Definitive-Guide-Cortex-M",
            "source_title": "The Definitive Guide to ARM Cortex-M3 and Cortex-M4 Processors (Joseph Yiu)",
            "source_type": "textbook",
            "source_reference": "Yiu, 3rd Ed., Chapter 7: Exceptions and Interrupts"
        },
        {
            "id": "chunk_drdo_fund_emb_02",
            "role_id": "scientist_b_ece",
            "competency": "embedded_realtime_systems",
            "stage": "fundamentals",
            "difficulty_level": 2,
            "domain": "electronics_radar",
            "discipline": "Electronics & Communication Engineering",
            "topic": "Bare-Metal Super-Loop vs Real-Time Operating Systems",
            "title": "Architectural Trade-Offs: Bare-Metal Polling vs RTOS Multitasking",
            "content": "Embedded architectures choose between bare-metal super-loops (cyclic executive) and preemptive RTOS kernels. A super-loop executes tasks sequentially inside a continuous while(1) loop, occasionally supplemented by timer interrupts. It features zero RAM overhead for task stacks, zero kernel context-switch overhead, and deterministic execution for trivial systems. However, super-loops scale poorly: response time for any task is bounded by the worst-case execution time (WCET) of all other loop tasks. Preemptive RTOS kernels provide deterministic responsiveness for high-priority tasks at the cost of stack memory overhead per task, kernel tick jitter, and synchronization complexity.",
            "expected_concepts": ["Bare-Metal vs RTOS", "cyclic executive", "worst-case execution time", "context switch overhead"],
            "sample_questions": [
                "What are the primary criteria that justify moving an embedded system design from a bare-metal super-loop to a preemptive RTOS?",
                "How does the worst-case response time of an event in a cyclic executive compare to a priority-preemptive RTOS?",
                "What memory and CPU overheads are introduced when a preemptive RTOS kernel is adopted?"
            ],
            "rubric": {
                "poor": "Believes an RTOS always makes the CPU run faster; unaware of task stack overhead or scheduling latency.",
                "acceptable": "Explains that RTOS enables priority preemption for time-critical tasks while super-loops suffer from execution delays of preceding functions.",
                "excellent": "Analyzes worst-case execution time (WCET), RAM footprint of per-task stacks, scheduler CPU utilization, and determinism under burst workloads."
            },
            "source": "Laplante-Real-Time-Systems",
            "source_title": "Real-Time Systems Design and Analysis (Phillip A. Laplante)",
            "source_type": "textbook",
            "source_reference": "Laplante, 4th Ed., Chapter 2: Hardware and Software Architecture"
        },
        {
            "id": "chunk_drdo_fund_dsp_01",
            "role_id": "scientist_b_ece",
            "competency": "digital_signal_processing",
            "stage": "fundamentals",
            "difficulty_level": 2,
            "domain": "electronics_radar",
            "discipline": "Electronics & Communication Engineering",
            "topic": "Nyquist-Shannon Sampling Theorem & Anti-Aliasing",
            "title": "Nyquist-Shannon Sampling Criterion, Aliasing Distortion, and Anti-Aliasing Filters",
            "content": "The Nyquist-Shannon Sampling Theorem states that a continuous-time bandlimited signal containing maximum frequency component f_max can be completely reconstructed from its samples without loss of information if and only if the sampling frequency f_s satisfies f_s > 2 * f_max (Nyquist rate). If f_s < 2 * f_max, spectral components above f_s/2 (Nyquist frequency) fold back into the baseband spectrum as irreversible aliased spectral artifacts. To prevent aliasing before Analog-to-Digital Conversion (ADC), an analog low-pass Anti-Aliasing Filter (AAF) must be placed in front of the ADC to attenuate all frequencies exceeding f_s/2 below the ADC's dynamic range floor.",
            "expected_concepts": ["Nyquist-Shannon Sampling Theorem", "aliasing foldover", "anti-aliasing filter", "sampling rate"],
            "sample_questions": [
                "State the Nyquist-Shannon Sampling Theorem and describe mathematically what occurs in the frequency domain when sampling below the Nyquist rate.",
                "Why must the anti-aliasing filter be implemented as an analog hardware stage before the ADC rather than as a digital filter after conversion?",
                "If a signal contains a 12 kHz interference tone and is sampled at 20 kHz without an anti-aliasing filter, at what frequency does the alias appear in the digitized output?"
            ],
            "rubric": {
                "poor": "Cannot state Nyquist rate; suggests filtering aliasing digitally after sampling; cannot calculate alias frequency.",
                "acceptable": "States fs >= 2*fmax; explains that high frequencies fold into lower bands; calculates alias frequency as |12 - 20| = 8 kHz.",
                "excellent": "Illustrates periodic spectral replication of sampled signals, proves irrecoverability once digitized, and designs analog filter roll-off relative to ADC SNR."
            },
            "source": "Oppenheim-Schafer-Discrete-Signal-Processing",
            "source_title": "Discrete-Time Signal Processing (Alan V. Oppenheim, Ronald W. Schafer)",
            "source_type": "textbook",
            "source_reference": "Oppenheim & Schafer, 3rd Ed., Chapter 4: Sampling of Continuous-Time Signals"
        },
        {
            "id": "chunk_drdo_fund_dsp_02",
            "role_id": "scientist_b_ece",
            "competency": "digital_signal_processing",
            "stage": "fundamentals",
            "difficulty_level": 2,
            "domain": "electronics_radar",
            "discipline": "Electronics & Communication Engineering",
            "topic": "Discrete Fourier Transform (DFT) and Fast Fourier Transform (FFT)",
            "title": "Discrete Fourier Transform (DFT) Properties and FFT Computational Complexity",
            "content": "The Discrete Fourier Transform (DFT) converts a discrete-time sequence x[n] of length N into its discrete frequency spectrum X[k]. Direct computation of an N-point DFT requires N^2 complex multiplications and N(N-1) complex additions. The Cooley-Tukey Fast Fourier Transform (FFT) algorithm exploits the periodicity and symmetry properties of the twiddle factor W_N = e^(-j*2*pi/N) to recursively decompose an N-point DFT into smaller sub-transforms, reducing computational complexity from O(N^2) to O(N log2 N). In radar signal processing, the FFT is the foundational engine for Range FFT, Doppler FFT, and pulse compression.",
            "expected_concepts": ["Discrete Fourier Transform / FFT", "twiddle factor", "computational complexity", "frequency bins"],
            "sample_questions": [
                "What is the mathematical definition of the Discrete Fourier Transform, and why is direct evaluation computationally prohibitive for real-time systems?",
                "How does the Cooley-Tukey Radix-2 FFT exploit twiddle factor symmetry to achieve O(N log2 N) operations?",
                "If a radar receiver takes 1024 samples at 10 MHz sampling rate, what is the frequency resolution of each FFT bin?"
            ],
            "rubric": {
                "poor": "Cannot explain DFT; unaware of O(N^2) vs O(N log N) complexity differences; cannot compute frequency bin width.",
                "acceptable": "States O(N^2) for DFT and O(N log N) for FFT; computes bin resolution as fs/N = 10 MHz / 1024 = ~9.76 kHz.",
                "excellent": "Derives decimation-in-time decomposition, explains butterfly operations and bit-reversal addressing, and analyzes fixed-point bit growth during butterfly stages."
            },
            "source": "Proakis-Manolakis-DSP",
            "source_title": "Digital Signal Processing: Principles, Algorithms, and Applications",
            "source_type": "textbook",
            "source_reference": "Proakis & Manolakis, 4th Ed., Chapter 7: The Discrete Fourier Transform"
        },
        {
            "id": "chunk_drdo_fund_rf_01",
            "role_id": "scientist_b_ece",
            "competency": "radar_rf_systems",
            "stage": "fundamentals",
            "difficulty_level": 2,
            "domain": "electronics_radar",
            "discipline": "Electronics & Communication Engineering",
            "topic": "Radar Range Equation and Power-Aperture Product",
            "title": "The Radar Range Equation, Received Echo Power, and Fourth-Power Law",
            "content": "The fundamental Radar Range Equation governs the received echo power P_r from a target of Radar Cross Section (RCS) sigma at range R: P_r = (P_t * G_t * G_r * lambda^2 * sigma) / ((4*pi)^3 * R^4 * L), where P_t is transmitted peak power, G_t and G_r are transmit/receive antenna gains, lambda is the operating wavelength, and L represents system losses. The inverse fourth-power dependence (1/R^4) arises because the transmitted electromagnetic wave experiences spherical spreading in both the forward propagation path (1/R^2) and the reradiated scattered return path (1/R^2). Consequently, doubling radar detection range requires a sixteen-fold (16x or +12 dB) increase in transmitter power or equivalent improvement in antenna gain/aperture.",
            "expected_concepts": ["Radar Range Equation", "fourth power distance", "radar cross section", "antenna gain"],
            "sample_questions": [
                "Derive or state the fundamental Radar Range Equation and explain why received signal power decreases with the fourth power of target distance.",
                "If a radar system's transmitter power is increased by a factor of 16 while all other parameters remain constant, what is the resulting percentage increase in maximum detection range?",
                "What physical factors contribute to system losses (L) in the radar range equation?"
            ],
            "rubric": {
                "poor": "Claims received power decays as 1/R^2 like communications; cannot state parameters of the radar equation.",
                "acceptable": "States 1/R^4 dependence due to two-way propagation; calculates 16^(1/4) = 2 (doubling or 100% increase in range).",
                "excellent": "Provides complete mathematical derivation from power density to receiver aperture, detailing antenna effective area A_e = G*lambda^2/(4*pi) and atmospheric/waveguide losses."
            },
            "source": "Skolnik-Radar-Handbook",
            "source_title": "Introduction to Radar Systems (Merrill I. Skolnik)",
            "source_type": "textbook",
            "source_reference": "Skolnik, 3rd Ed., Chapter 1: Nature of Radar and the Radar Equation"
        },
        {
            "id": "chunk_drdo_fund_rf_02",
            "role_id": "scientist_b_ece",
            "competency": "radar_rf_systems",
            "stage": "fundamentals",
            "difficulty_level": 2,
            "domain": "electronics_radar",
            "discipline": "Electronics & Communication Engineering",
            "topic": "Pulse Repetition Frequency (PRF) and Unambiguous Range",
            "title": "Pulse Repetition Frequency (PRF), Pulse Repetition Interval (PRI), and Maximum Unambiguous Range",
            "content": "Pulsed radars transmit periodic electromagnetic bursts characterized by Pulse Width (tau), Pulse Repetition Interval (PRI = T), and Pulse Repetition Frequency (PRF = 1/T). The maximum unambiguous range R_unamb is the maximum target distance from which an echo can return before the subsequent pulse is transmitted: R_unamb = c * PRI / 2 = c / (2 * PRF). Targets located beyond R_unamb generate 'second-time-around' (range-ambiguous) returns. However, higher PRFs are required for high unambiguous Doppler velocity measurement (v_unamb = lambda * PRF / 4). This inherent conflict between range and velocity ambiguities is the classic Radar Ambiguity dilemma, resolved through multiple PRFs (staggered PRF techniques).",
            "expected_concepts": ["Pulse Repetition Frequency (PRF)", "unambiguous range", "two-way time of flight", "staggered PRF"],
            "sample_questions": [
                "How is the maximum unambiguous detection range of a pulsed radar calculated from its PRF?",
                "If a pulsed radar operates at a PRF of 1 kHz, what is its maximum unambiguous range?",
                "Explain the fundamental trade-off between maximizing unambiguous range and maximizing unambiguous Doppler velocity in pulsed radars."
            ],
            "rubric": {
                "poor": "Forgets the factor of 2 for round-trip travel; unable to calculate unambiguous range from PRF.",
                "acceptable": "Uses R = c/(2*PRF); calculates c/(2000) = 300,000 km/s / 2000 = 150 km; explains echo arriving after next pulse.",
                "excellent": "Analyzes the PRF dilemma (R_unamb * v_unamb = c * lambda / 8), explains blind speeds, and details PRF jittering / Chinese Remainder Theorem for ambiguity resolution."
            },
            "source": "Skolnik-Radar-Handbook",
            "source_title": "Radar Handbook (Merrill I. Skolnik)",
            "source_type": "reference",
            "source_reference": "Skolnik, 3rd Ed., Chapter 2: MTI and Pulse Doppler Radar"
        },

        # --- Stage 4: Core Technical / Role Technical ---
        {
            "id": "chunk_drdo_tech_emb_01",
            "role_id": "scientist_b_ece",
            "competency": "embedded_realtime_systems",
            "stage": "role_technical",
            "difficulty_level": 3,
            "domain": "electronics_radar",
            "discipline": "Electronics & Communication Engineering",
            "topic": "Priority Inversion and Priority Ceiling / Inheritance Protocols",
            "title": "Priority Inversion Phenomenon, Unbounded Latency, and Ceiling Protocols in RTOS",
            "content": "Priority inversion is a dangerous failure mode in real-time preemptive kernels where a high-priority task is indirectly preempted and delayed by a medium-priority task. This occurs when a low-priority task L acquires a shared mutual exclusion resource (mutex M). High-priority task H arrives, preempts L, and subsequently requests M. Because M is locked, H blocks waiting for L to release it. Before L can complete its critical section, an unrelated medium-priority task M_mid (which does not use M) preempts L because M_mid has higher priority than L. Consequently, H is blocked indefinitely while M_mid executes, violating real-time determinism (as famously occurred on the Mars Pathfinder spacecraft in 1997). The two standard mitigation protocols are: 1. Priority Inheritance Protocol (PIP): Task L temporarily inherits the priority of task H while holding resource M. 2. Priority Ceiling Protocol (PCP): Every mutex is assigned a priority ceiling equal to the highest priority of any task that may lock it; a task can only lock a mutex if its priority is strictly higher than the ceilings of all currently locked mutexes, which mathematically prevents deadlock and bounds blocking to at most one critical section.",
            "expected_concepts": ["Priority Inversion & Ceiling Protocol", "priority inheritance", "unbounded latency", "mutex deadlock prevention"],
            "sample_questions": [
                "What is priority inversion in real-time operating systems, and how can an unrelated medium-priority task cause a high-priority task to miss its deadline?",
                "How does the Priority Inheritance Protocol resolve priority inversion, and what edge-case limitations does it still have?",
                "Compare Priority Inheritance Protocol (PIP) with the Immediate Priority Ceiling Protocol (IPCP) in terms of deadlock prevention and implementation complexity."
            ],
            "rubric": {
                "poor": "Cannot explain how a medium-priority task causes unbounded blocking; suggests disabling all interrupts as the only fix.",
                "acceptable": "Walks through Low -> acquires lock -> High blocks -> Medium preempts Low; explains that Priority Inheritance raises Low's priority to High.",
                "excellent": "Demonstrates why PIP does not prevent deadlocks or chained blocking; explains how Ceiling Priority Protocol guarantees deadlock freedom and bounds priority inversion to at most one critical section duration."
            },
            "source": "Sha-Rajkumar-Lehoczky-Priority-Inversion",
            "source_title": "Priority Inheritance Protocols: An Approach to Real-Time Synchronization (L. Sha, R. Rajkumar, J. P. Lehoczky)",
            "source_type": "ieee_paper",
            "source_reference": "IEEE Transactions on Computers, Vol. 39, No. 9, Sept 1990"
        },
        {
            "id": "chunk_drdo_tech_emb_02",
            "role_id": "scientist_b_ece",
            "competency": "embedded_realtime_systems",
            "stage": "role_technical",
            "difficulty_level": 3,
            "domain": "electronics_radar",
            "discipline": "Electronics & Communication Engineering",
            "topic": "Watchdog Timers and System Hang Fault Recovery",
            "title": "Hardware Watchdog Timers, Windowed Watchdogs, and Failure Recovery in Mission-Critical Embedded Systems",
            "content": "A Watchdog Timer (WDT) is an autonomous hardware counter clocked independently of the main CPU clock (often using an internal dedicated Low-Power Oscillator - LSI/LPO). The counter continuously counts down from a configured reload value toward zero. Under normal software execution, the firmware must periodically 'kick' or 'refresh' the watchdog counter before it reaches zero. If the software hangs due to infinite loops, deadlocks, stack overflows, or electrostatic discharge (ESD) soft errors, the watchdog counter expires and asserts a hardware system reset line to recover the processor. In safety-critical aerospace and defence systems, Windowed Watchdog Timers (WWDT) are required: the refresh must occur within an allowed time window (neither too late NOR too early). An early refresh indicates timing runaway or rogue loop execution, triggering an immediate fault reset.",
            "expected_concepts": ["Watchdog Timers", "windowed watchdog", "hardware supervisor", "deadlock recovery"],
            "sample_questions": [
                "How does an independent hardware watchdog timer detect firmware hangs, and why must its clock source be independent from the main system PLL?",
                "What failure modes does a Windowed Watchdog Timer (WWDT) catch that a conventional standard watchdog timer fails to detect?",
                "In a multi-tasking RTOS, why is it bad practice to kick the watchdog from a single dedicated high-priority timer task?"
            ],
            "rubric": {
                "poor": "Thinks a watchdog is just a software timer interrupt; unaware that kicking from a high-priority task masks hangs in worker tasks.",
                "acceptable": "Explains that watchdog resets the MCU on hang; explains that windowed watchdogs enforce both min and max refresh time bounds.",
                "excellent": "Details health-monitoring check-in patterns where each RTOS worker task reports heartbeats to a supervisor before kicking, and explains independent oscillator isolation against main PLL lock failure."
            },
            "source": "Ganssle-Watchdog-Design",
            "source_title": "Designing Great Watchdog Timers for Embedded Systems (Jack Ganssle)",
            "source_type": "technical_reference",
            "source_reference": "Embedded Systems Programming / Ganssle Group Technical Report"
        },
        {
            "id": "chunk_drdo_tech_emb_03",
            "role_id": "scientist_b_ece",
            "competency": "embedded_realtime_systems",
            "stage": "role_technical",
            "difficulty_level": 3,
            "domain": "electronics_radar",
            "discipline": "Electronics & Communication Engineering",
            "topic": "Direct Memory Access (DMA) Scatter-Gather for Sensor Telemetry",
            "title": "Direct Memory Access (DMA) Architectures, Circular Buffering, and Scatter-Gather Ingestion",
            "content": "High-throughput sensor systems (such as radar ADC interfaces, telemetry serial buses, and gigabit Ethernet controllers) generate data rates that would overwhelm a CPU if transferred byte-by-byte via interrupt-driven I/O. Direct Memory Access (DMA) controllers take ownership of the system bus to transfer blocks of data directly between peripheral FIFO buffers and system SRAM without CPU intervention. Advanced DMA controllers support Scatter-Gather operations using linked-list descriptor tables in memory, enabling automated transfers across non-contiguous physical RAM buffers without requiring software reconfiguration per block. Double buffering (ping-pong buffers) allows the DMA to fill Buffer B while the CPU/DSP processes Buffer A, eliminating race conditions and minimizing transfer latency.",
            "expected_concepts": ["DMA Scatter-Gather", "ping-pong double buffer", "bus mastering", "cache coherency"],
            "sample_questions": [
                "How does Direct Memory Access (DMA) offload the CPU in high-speed sensor data acquisition systems?",
                "Explain the operational architecture of a Ping-Pong (double buffer) DMA scheme and how it prevents data tearing.",
                "What cache coherency challenges arise when a DMA controller writes data to SRAM on a microcontroller featuring a data cache (D-Cache)?"
            ],
            "rubric": {
                "poor": "Cannot explain DMA; unaware of double buffering or why CPU cannot read a buffer while DMA is writing to it.",
                "acceptable": "Explains hardware bus transfer without CPU; describes ping-pong buffer switching between read and write pointers.",
                "excellent": "Analyzes cache invalidation requirements before CPU reads DMA buffers, explains scatter-gather descriptor chains, and computes bus bandwidth saturation."
            },
            "source": "Yiu-Definitive-Guide-Cortex-M",
            "source_title": "The Definitive Guide to ARM Cortex-M7 and Cortex-M4 (Joseph Yiu)",
            "source_type": "textbook",
            "source_reference": "Yiu, Chapter 15: Memory System and Direct Memory Access"
        },
        {
            "id": "chunk_drdo_tech_dsp_01",
            "role_id": "scientist_b_ece",
            "competency": "digital_signal_processing",
            "stage": "role_technical",
            "difficulty_level": 3,
            "domain": "electronics_radar",
            "discipline": "Electronics & Communication Engineering",
            "topic": "FIR vs IIR Digital Filter Design and Phase Linearity",
            "title": "Finite Impulse Response (FIR) vs Infinite Impulse Response (IIR) Digital Filters",
            "content": "Digital filters fall into two fundamental classes: Finite Impulse Response (FIR) and Infinite Impulse Response (IIR). FIR filters depend only on present and past input samples (non-recursive: y[n] = sum_{k=0}^{M-1} b_k * x[n-k]). FIR filters have strictly linear phase characteristics when coefficient symmetry is maintained (b_k = b_{M-1-k}), meaning all frequency components undergo identical group delay, preventing pulse shape distortion—an indispensable requirement for pulsed radar pulse compression. Furthermore, FIR filters are inherently stable because all system poles reside at the origin z = 0. In contrast, IIR filters include feedback (recursive: y[n] = sum b_k x[n-k] - sum a_m y[n-m]). They achieve much sharper roll-off for a significantly lower order (fewer MACs) than equivalent FIR filters, but exhibit non-linear phase distortion and risk instability due to finite word-length coefficient quantization shifting poles outside the unit circle |z| >= 1.",
            "expected_concepts": ["FIR vs IIR Digital Filters", "linear phase", "group delay", "filter stability", "pole-zero constellation"],
            "sample_questions": [
                "Contrast FIR and IIR digital filters in terms of stability, phase linearity, computational complexity, and feedback structure.",
                "Why is strictly linear phase essential in radar pulse compression receivers, and which filter architecture guarantees it?",
                "How does finite word-length coefficient quantization affect the stability of an IIR filter compared to an FIR filter?"
            ],
            "rubric": {
                "poor": "Confuses FIR and IIR; claims IIR filters are always stable; unaware of group delay concepts.",
                "acceptable": "Identifies that FIR is non-recursive with no poles outside origin (always stable) and linear phase; IIR has feedback and is cheaper computationally.",
                "excellent": "Derives group delay d(theta)/d(omega) for symmetric coefficients, explains radar pulse distortion from non-linear phase, and demonstrates pole migration outside the unit circle under quantization."
            },
            "source": "Oppenheim-Schafer-Discrete-Signal-Processing",
            "source_title": "Discrete-Time Signal Processing (Alan V. Oppenheim, Ronald W. Schafer)",
            "source_type": "textbook",
            "source_reference": "Oppenheim & Schafer, 3rd Ed., Chapter 7: Filter Design Techniques"
        },
        {
            "id": "chunk_drdo_tech_dsp_02",
            "role_id": "scientist_b_ece",
            "competency": "digital_signal_processing",
            "stage": "role_technical",
            "difficulty_level": 3,
            "domain": "electronics_radar",
            "discipline": "Electronics & Communication Engineering",
            "topic": "Fixed-Point Quantization, Dynamic Range, and Limit Cycles",
            "title": "Fixed-Point Arithmetic, Quantization Noise, Dynamic Range, and Limit Cycles in DSP",
            "content": "In embedded defence hardware, algorithms are frequently implemented on fixed-point DSPs or FPGAs for power efficiency and high throughput. Fixed-point numbers represent values using Q-format (e.g., Q1.15 for 16-bit signed integers). Converting continuous real numbers to fixed-point introduces quantization error, modeled as additive white noise with variance sigma_e^2 = Delta^2 / 12, where Delta = 2^(-B) is the least significant bit (LSB) quantization step. Each additional bit provides approximately 6.02 dB of signal-to-quantization-noise ratio (SQNR). Fixed-point filters also suffer from overflow (wrap-around vs saturation arithmetic) and limit cycle oscillations (granular noise or overflow oscillations) caused by non-linearities in recursive feedback loops.",
            "expected_concepts": ["Fixed-Point Quantization", "dynamic range", "overflow saturation", "limit cycles", "SQNR 6 dB per bit"],
            "sample_questions": [
                "Derive or explain the rule of thumb that each additional bit in fixed-point ADC/DSP yields ~6.02 dB of dynamic range.",
                "What are limit cycle oscillations in recursive IIR digital filters, and what design techniques prevent them?",
                "Explain the difference between wrap-around (two's complement) overflow and saturation arithmetic in DSP accumulators."
            ],
            "rubric": {
                "poor": "Cannot explain what Q-format or quantization noise is; unaware of saturation arithmetic.",
                "acceptable": "Explains that rounding introduces quantization error; states SQNR ~= 6.02*B + 1.76 dB; explains saturation clamping.",
                "excellent": "Derives quantization variance Delta^2/12, explains zero-input limit cycles from non-linear truncation in recursive feedback, and details scaling to prevent overflow."
            },
            "source": "Proakis-Manolakis-DSP",
            "source_title": "Digital Signal Processing: Principles, Algorithms, and Applications",
            "source_type": "textbook",
            "source_reference": "Proakis & Manolakis, 4th Ed., Chapter 9: Implementation of Discrete-Time Systems"
        },
        {
            "id": "chunk_drdo_tech_dsp_03",
            "role_id": "scientist_b_ece",
            "competency": "digital_signal_processing",
            "stage": "role_technical",
            "difficulty_level": 3,
            "domain": "electronics_radar",
            "discipline": "Electronics & Communication Engineering",
            "topic": "Digital Pulse Compression and Matched Filtering",
            "title": "Digital Pulse Compression, Linear Frequency Modulation (Chirp), and Matched Filtering",
            "content": "Pulsed radar systems face a fundamental design contradiction between detection range and range resolution. Detection range depends on total transmitted energy (P_peak * tau), requiring long pulse width tau. Conversely, range resolution Delta_R = c * tau / 2 requires an extremely short pulse width. Digital Pulse Compression resolves this dilemma by modulating the carrier frequency within a long pulse tau over bandwidth B, most commonly using Linear Frequency Modulation (LFM or 'chirp': f(t) = f_0 + mu*t). In the receiver, the digitized echo is passed through a Matched Filter whose impulse response is the time-reversed complex conjugate of the transmitted chirp: h(t) = s^*(-t). The matched filter output compresses the long pulse of duration tau into a narrow sinc envelope of effective width tau_comp = 1/B. The resulting range resolution becomes Delta_R = c / (2 * B), completely decoupled from pulse duration. The pulse compression ratio (time-bandwidth product B*tau) represents the processing gain (SNR improvement in dB: 10*log10(B*tau)).",
            "expected_concepts": ["Digital Pulse Compression", "matched filter", "linear frequency modulation", "time-bandwidth product", "range resolution"],
            "sample_questions": [
                "Explain the radar designer's dilemma between detection range and range resolution, and how Linear Frequency Modulation (LFM) chirp resolves it.",
                "Mathematically define the transfer function or impulse response of a Matched Filter and explain why it maximizes output Signal-to-Noise Ratio (SNR).",
                "If a radar transmits a 50 microsecond chirp pulse across a bandwidth of 20 MHz, what is the pulse compression ratio and the achievable range resolution?"
            ],
            "rubric": {
                "poor": "Cannot explain pulse compression; believes shorter pulses give greater detection range; unaware of matched filtering.",
                "acceptable": "Explains that frequency modulation widens bandwidth while keeping pulse long; computes compression ratio = 50e-6 * 20e6 = 1000 (30 dB); computes resolution c/(2B) = 7.5 meters.",
                "excellent": "Derives the matched filter SNR maximization via Cauchy-Schwarz inequality, analyzes range sidelobes, and explains Doppler tolerance of LFM waveforms."
            },
            "source": "Skolnik-Radar-Handbook",
            "source_title": "Radar Handbook (Merrill I. Skolnik)",
            "source_type": "reference",
            "source_reference": "Skolnik, 3rd Ed., Chapter 8: Pulse Compression Radar"
        },
        {
            "id": "chunk_drdo_tech_rf_01",
            "role_id": "scientist_b_ece",
            "competency": "radar_rf_systems",
            "stage": "role_technical",
            "difficulty_level": 3,
            "domain": "electronics_radar",
            "discipline": "Electronics & Communication Engineering",
            "topic": "Doppler Frequency Shift and Moving Target Indication (MTI)",
            "title": "Doppler Frequency Shift, Moving Target Indication (MTI), and Clutter Rejection Filters",
            "content": "When a radar illuminates a moving target with radial velocity v_r, the received echo exhibits a Doppler frequency shift f_d = 2 * v_r * f_0 / c = 2 * v_r / lambda. Stationary clutter (ground, buildings, rain) generates returns with zero or near-zero Doppler frequency (f_d = 0). Moving Target Indication (MTI) uses high-pass digital delay-line cancelers (e.g., single delay-line canceler: y[n] = x[n] - x[n-1]) to notch out static returns at DC while passing Doppler-shifted echoes from airborne targets. A critical operational hazard in MTI radar is 'blind speeds'—velocities where the Doppler frequency is an exact integer multiple of the PRF (f_d = k * PRF), causing the target return to be canceled identically like stationary clutter: v_blind = k * lambda * PRF / 2. Radars eliminate blind speeds using staggered PRF sequences.",
            "expected_concepts": ["Doppler Frequency Shift", "moving target indication", "delay line canceler", "blind speeds", "clutter rejection"],
            "sample_questions": [
                "Derive the Doppler frequency shift formula for a radar target moving with radial velocity v_r at carrier wavelength lambda.",
                "How does an MTI delay-line canceler filter eliminate stationary ground clutter from moving target echoes?",
                "What is a radar 'blind speed', and how does staggered PRF transmission eliminate blind speeds in airspace surveillance?"
            ],
            "rubric": {
                "poor": "Cannot state Doppler formula f_d = 2*v/lambda; confused about why clutter is at zero frequency; unaware of blind speeds.",
                "acceptable": "States f_d = 2*v_r / lambda; explains subtraction of successive pulses to cancel static objects; defines blind speed as f_d = n*PRF.",
                "excellent": "Derives the frequency response |H(f)| = 2*|sin(pi*f/PRF)| of the delay-line canceler, plots filter notch depth, and explains multi-PRI stagger optimization."
            },
            "source": "Skolnik-Radar-Handbook",
            "source_title": "Introduction to Radar Systems (Merrill I. Skolnik)",
            "source_type": "textbook",
            "source_reference": "Skolnik, 3rd Ed., Chapter 3: MTI and Pulse Doppler"
        },
        {
            "id": "chunk_drdo_tech_rf_02",
            "role_id": "scientist_b_ece",
            "competency": "radar_rf_systems",
            "stage": "role_technical",
            "difficulty_level": 3,
            "domain": "electronics_radar",
            "discipline": "Electronics & Communication Engineering",
            "topic": "Frequency Modulated Continuous Wave (FMCW) Principles",
            "title": "Frequency Modulated Continuous Wave (FMCW) Radar Principles and Beat Frequency Extraction",
            "content": "Unlike pulsed radars, FMCW radars transmit continuous electromagnetic energy whose frequency is modulated linearly with time (sawtooth or triangular waveform). The echo returning from a target at range R arrives after a round-trip time delay tau = 2*R/c. In the receiver, the received echo is mixed (homodyne downconversion) with a sample of the currently transmitted chirp. The output of the mixer produces a difference frequency known as the Beat Frequency f_b. For a modulation sweep bandwidth B and sweep duration T_m: f_b = (2 * R / c) * (B / T_m). Measuring f_b via an FFT directly reveals target range. For moving targets, the beat frequency incorporates both range and Doppler components (f_b_up = |f_r - f_d|, f_b_down = |f_r + f_d|), which triangular modulation uncouples by comparing upward and downward frequency ramps.",
            "expected_concepts": ["FMCW Radar Principles", "beat frequency", "sweep bandwidth", "homodyne mixer", "triangular modulation"],
            "sample_questions": [
                "Explain the operational principle of FMCW radar and derive the formula relating beat frequency f_b to target range R.",
                "Why is FMCW radar widely used for altimeters and millimeter-wave proximity sensors compared to pulsed radars?",
                "How does triangular frequency modulation separate target range from target Doppler velocity in an FMCW radar?"
            ],
            "rubric": {
                "poor": "Cannot explain beat frequency; confuses pulsed radar time-of-flight with FMCW frequency mixing.",
                "acceptable": "Explains frequency difference between transmitted and delayed echo; states f_b = (2*R/c)*(B/T_m); explains low peak power advantage.",
                "excellent": "Derives the two-equation system for triangular modulation ramps (f_up and f_down) to simultaneously solve for range and radial velocity without ambiguity."
            },
            "source": "Skolnik-Radar-Handbook",
            "source_title": "Radar Handbook (Merrill I. Skolnik)",
            "source_type": "reference",
            "source_reference": "Skolnik, Chapter 14: CW and FMCW Radar"
        },
        {
            "id": "chunk_drdo_tech_rf_03",
            "role_id": "scientist_b_ece",
            "competency": "radar_rf_systems",
            "stage": "role_technical",
            "difficulty_level": 3,
            "domain": "electronics_radar",
            "discipline": "Electronics & Communication Engineering",
            "topic": "Receiver Dynamic Range, Noise Figure, and Friis Equation",
            "title": "Radar Receiver Sensitivity, Noise Figure, and Friis Formula for Cascaded Stages",
            "content": "The sensitivity of a radar receiver is bounded by thermal noise power P_n = k * T_0 * B * F, where k is Boltzmann's constant, T_0 = 290 K is standard reference temperature, B is receiver noise bandwidth, and F is the receiver Noise Figure. In a multistage superheterodyne RF front-end (Low Noise Amplifier, RF filter, mixer, IF amplifier), Friis' Formula for Cascaded Noise Figure governs total noise performance: F_total = F_1 + (F_2 - 1)/G_1 + (F_3 - 1)/(G_1 * G_2) + ... This proves that the first stage (the LNA) dominantly determines overall system noise figure, provided the LNA has sufficient power gain G_1. Dynamic range (such as Spurious-Free Dynamic Range - SFDR) defines the power span between the minimum detectable signal (MDS) and the input level where third-order intermodulation products (IP3) rise above the noise floor.",
            "expected_concepts": ["Receiver Dynamic Range", "noise figure", "Friis formula", "low noise amplifier", "spurious free dynamic range"],
            "sample_questions": [
                "State Friis' Formula for cascaded stages and explain why the first RF amplifier (LNA) dominates the entire receiver noise figure.",
                "What is Spurious-Free Dynamic Range (SFDR), and why is high SFDR critical when detecting small RCS targets in the presence of strong jammer signals?",
                "Calculate the thermal noise floor in dBm for a receiver with 5 MHz bandwidth and an overall noise figure of 4 dB at 290 K."
            ],
            "rubric": {
                "poor": "Cannot write Friis formula; unaware that thermal noise is kTB; confuses noise figure with gain.",
                "acceptable": "Writes F = F1 + (F2-1)/G1; explains that high LNA gain suppresses downstream noise contributions; computes kTB ~= -174 dBm/Hz + 10*log10(5e6) + 4 dB.",
                "excellent": "Calculates exact noise floor (-174 + 67 + 4 = -103 dBm), analyzes 1 dB compression point vs IIP3, and explains dynamic range trade-offs in direct RF sampling ADCs."
            },
            "source": "Pozar-Microwave-Engineering",
            "source_title": "Microwave Engineering (David M. Pozar)",
            "source_type": "textbook",
            "source_reference": "Pozar, 4th Ed., Chapter 10: Noise and Active RF Components"
        },
        {
            "id": "chunk_drdo_tech_av_01",
            "role_id": "scientist_b_ece",
            "competency": "avionics_communication",
            "stage": "role_technical",
            "difficulty_level": 3,
            "domain": "electronics_radar",
            "discipline": "Electronics & Communication Engineering",
            "topic": "MIL-STD-1553B Dual-Redundant Serial Data Bus",
            "title": "MIL-STD-1553B Dual-Redundant Avionics Multiplex Data Bus Architecture",
            "content": "MIL-STD-1553B is the standard military avionics communication bus defining mechanical, electrical, and functional characteristics for dual-redundant multiplex data buses. Operating at a 1.0 Mbps bit rate over shielded twisted-pair wire using Manchester II bi-phase coding, the bus employs differential signaling transformer coupling to ensure high common-mode noise rejection and galvanic isolation. The architecture is strictly command-response: exactly one designated Bus Controller (BC) initiates all message transactions; up to 31 Remote Terminals (RTs) and passive Bus Monitors (BMs) respond only when explicitly polled. A message consists of 20-bit words (Command, Data, Status words), each comprising a 3-bit synchronization sync pattern, 16 data/command bits, and 1 parity bit. Dual redundancy (Bus A and Bus B) ensures that if one physical cable is severed or shorted, communication switches seamlessly to the alternate channel without data loss.",
            "expected_concepts": ["MIL-STD-1553B Dual-Redundant Bus", "bus controller", "remote terminal", "Manchester II encoding", "transformer coupling"],
            "sample_questions": [
                "Describe the architectural topology of a MIL-STD-1553B avionics bus and explain the roles of Bus Controller (BC) and Remote Terminal (RT).",
                "Why does MIL-STD-1553B employ Manchester II bi-phase encoding and transformer coupling rather than standard non-return-to-zero (NRZ) UART signaling?",
                "What is the structure of a 20-bit MIL-STD-1553B word, and how does the receiver distinguish Command words from Data words?"
            ],
            "rubric": {
                "poor": "Confuses 1553B with CAN bus or Ethernet; unaware of master-slave command-response protocol; cannot explain dual redundancy.",
                "acceptable": "Explains Bus Controller coordinates all transfers to Remote Terminals at 1 Mbps; mentions Manchester encoding and transformer isolation for noise immunity.",
                "excellent": "Details word structure (3-bit sync, 16 payload, 1 parity), explains sync polarity inversion distinguishing command/status from data words, and describes failover policies between Bus A and Bus B."
            },
            "source": "MIL-STD-1553B-Standard",
            "source_title": "Digital Time Division Command/Response Multiplex Data Bus (DoD Standard)",
            "source_type": "official_standard",
            "source_reference": "MIL-STD-1553B Notice 2, Department of Defense, USA"
        },
        {
            "id": "chunk_drdo_tech_av_02",
            "role_id": "scientist_b_ece",
            "competency": "avionics_communication",
            "stage": "role_technical",
            "difficulty_level": 3,
            "domain": "electronics_radar",
            "discipline": "Electronics & Communication Engineering",
            "topic": "ARINC-429 Serial Avionics Interface",
            "title": "ARINC-429 Digital Information Transfer System Specifications and Word Format",
            "content": "ARINC-429 is the widely deployed commercial and military transport avionics specification for digital information transfer. In contrast to the multi-drop shared bus of MIL-STD-1553B, ARINC-429 is a simplex, point-to-point, single-transmitter multi-receiver architecture. Up to 20 receivers can listen on a single twisted shielded pair. Signaling uses Bipolar Return-to-Zero (BPRZ) modulation at either low speed (12.5 kbps) or high speed (100 kbps), with differential voltages switching between +10V (High), 0V (Null), and -10V (Low). Every transmission consists of a 32-bit word structured into five fields: 8-bit Label (identifying data type in octal, transmitted LSB first), 2-bit Source/Destination Identifier (SDI), 19-bit Data Payload, 2-bit Sign/Status Matrix (SSM), and 1 Parity bit (odd parity).",
            "expected_concepts": ["ARINC-429 Serial Protocol", "bipolar return to zero", "32-bit word format", "simplex point-to-point", "label octal encoding"],
            "sample_questions": [
                "Contrast the physical and operational topologies of ARINC-429 and MIL-STD-1553B.",
                "Explain the 32-bit word structure of an ARINC-429 message, detailing the purpose of the Label, SDI, and SSM fields.",
                "What is Bipolar Return-to-Zero (BPRZ) signaling, and what electrical advantage does it provide over standard NRZ signaling in aircraft wiring?"
            ],
            "rubric": {
                "poor": "Thinks ARINC-429 is a multi-master bus like CAN; unaware of 32-bit word or BPRZ signaling.",
                "acceptable": "Identifies ARINC-429 as point-to-point simplex (one transmitter, up to 20 listeners); outlines 32-bit word format with octal labels.",
                "excellent": "Draws BPRZ three-level waveform (+10V, 0V, -10V), explains self-clocking advantages, and analyzes SSM health status decoding."
            },
            "source": "ARINC-429-Specification",
            "source_title": "Mark 33 Digital Information Transfer System (DITS)",
            "source_type": "official_standard",
            "source_reference": "Aeronautical Radio, Inc. (ARINC) Specification 429 Part 1-17"
        },
        {
            "id": "chunk_drdo_tech_av_03",
            "role_id": "scientist_b_ece",
            "competency": "avionics_communication",
            "stage": "role_technical",
            "difficulty_level": 3,
            "domain": "electronics_radar",
            "discipline": "Electronics & Communication Engineering",
            "topic": "Phase Locked Loops (PLL) and RF Frequency Synthesis",
            "title": "Phase Locked Loops (PLL), Voltage Controlled Oscillators, and Frequency Synthesis in Radar Transceivers",
            "content": "Phase Locked Loops (PLL) are feedback control systems that generate stable, high-frequency local oscillator (LO) signals locked in phase and frequency to a low-noise reference oscillator (such as a Temperature Compensated Crystal Oscillator - TCXO). A classic integer-N PLL comprises a Phase Frequency Detector (PFD), a Charge Pump (CP), a low-pass Loop Filter, a Voltage Controlled Oscillator (VCO), and a digital feedback frequency divider (divide-by-N). The loop filter integrates charge pulses from the PFD, converting phase errors into a smooth DC control voltage V_tune that tunes the VCO. Phase noise in a PLL is determined by the reference oscillator and charge pump inside the loop bandwidth, and by the VCO outside the loop bandwidth. Fractional-N PLLs with Delta-Sigma modulators provide sub-Hz frequency resolution with fast settling time.",
            "expected_concepts": ["Phase Locked Loops (PLL)", "phase frequency detector", "charge pump loop filter", "phase noise", "local oscillator"],
            "sample_questions": [
                "Diagram the basic components of a Phase Locked Loop (PLL) frequency synthesizer and explain how frequency locking is achieved.",
                "How does the choice of loop filter bandwidth affect the trade-off between PLL lock settling time and reference spur attenuation?",
                "What is phase noise, and why is low phase noise in the receiver local oscillator vital for radar Doppler detection?"
            ],
            "rubric": {
                "poor": "Cannot name components of a PLL; confused about feedback loop operations; cannot explain phase noise.",
                "acceptable": "Outlines PFD, charge pump, loop filter, VCO, and divider; explains that loop filter converts phase error to control voltage.",
                "excellent": "Analyzes loop transfer function, details close-in vs far-out phase noise trade-offs across loop bandwidth, and explains reciprocal mixing masking weak Doppler returns."
            },
            "source": "Razavi-Design-of-Analog-CMOS",
            "source_title": "Design of Analog CMOS Integrated Circuits (Behzad Razavi)",
            "source_type": "textbook",
            "source_reference": "Razavi, 2nd Ed., Chapter 15: Phase-Locked Loops"
        },

        # --- Stage 5: Deep Dive ---
        {
            "id": "chunk_drdo_deep_emb_01",
            "role_id": "scientist_b_ece",
            "competency": "embedded_realtime_systems",
            "stage": "deep_dive",
            "difficulty_level": 4,
            "domain": "electronics_radar",
            "discipline": "Electronics & Communication Engineering",
            "topic": "Deterministic Jitter Mitigation, Cache Partitioning, and Hard Real-Time Execution",
            "title": "Mitigating Timing Jitter, Memory Bus Contention, and Cache Partitioning in High-Speed Radar Processors",
            "content": "In hard real-time radar control loops (e.g. beam steering controllers or pulse scheduling engines), timing jitter on interrupt servicing can cause catastrophic phase errors or missed radar pulses. In modern high-performance microprocessors (such as ARM Cortex-R or Cortex-A), sources of non-determinism include Instruction/Data Cache misses, Translation Lookaside Buffer (TLB) misses, multi-core memory bus contention, and out-of-order execution pipelines. To ensure microsecond-level hard real-time determinism, engineers employ Tightly Coupled Memory (TCM) for zero-wait-state interrupt handlers and critical data structures, lock down critical code lines in L1/L2 caches, configure static Memory Management Unit (MMU) flat-mapped page tables, and assign dedicated DMA memory channels that bypass CPU shared buses.",
            "expected_concepts": ["deterministic latency", "tightly coupled memory", "cache lockdown", "bus contention", "timing jitter"],
            "sample_questions": [
                "What architectural mechanisms in modern superscalar processors introduce timing jitter, and how do you guarantee microsecond determinism in radar pulse scheduling?",
                "Compare Tightly Coupled Memory (TCM) with standard L1 Cache in terms of access latency and execution determinism.",
                "How do you profile and measure Worst-Case Execution Time (WCET) on an embedded target processor to verify hard real-time safety compliance?"
            ],
            "rubric": {
                "poor": "Believes average execution time is sufficient; unaware of cache miss jitter or TCM architectures.",
                "acceptable": "Explains that cache misses and bus contention create latency variance; identifies TCM as predictable zero-wait-state memory.",
                "excellent": "Formulates formal WCET analysis techniques, details cache lockdown registers and AXI bus arbiter QoS configuration, and explains instruction pipeline serialization."
            },
            "source": "Laplante-Real-Time-Systems",
            "source_title": "Real-Time Systems Design and Analysis (Phillip A. Laplante)",
            "source_type": "textbook",
            "source_reference": "Laplante, 4th Ed., Chapter 6: Performance Analysis"
        },
        {
            "id": "chunk_drdo_deep_dsp_01",
            "role_id": "scientist_b_ece",
            "competency": "digital_signal_processing",
            "stage": "deep_dive",
            "difficulty_level": 4,
            "domain": "electronics_radar",
            "discipline": "Electronics & Communication Engineering",
            "topic": "Adaptive Beamforming and Spatial Null-Steering",
            "title": "Adaptive Beamforming Algorithms, Covariance Matrix Inversion, and Spatial Jammer Nulling",
            "content": "Adaptive beamforming uses an array of antenna sensor elements to dynamically adjust the complex weighting vector w = [w_1, w_2, ..., w_M]^T applied to digitized receiver channels. The goal is to steer the main beam peak toward the desired target of interest while simultaneously placing deep spatial nulls in the direction of hostile electronic countermeasures (jamming signals) and clutter. The optimal weight vector in Minimum Variance Distortionless Response (MVDR / Capon beamformer) is derived by minimizing output noise and interference power subject to a distortionless unity-gain constraint in the target direction: w = (R_xx^(-1) * a(theta_0)) / (a(theta_0)^H * R_xx^(-1) * a(theta_0)), where R_xx is the sample spatial covariance matrix and a(theta_0) is the array steering vector. In practical radar signal processors, computing R_xx^(-1) in real-time requires stable matrix decomposition (Cholesky decomposition or QR decomposition) to avoid ill-conditioned numerical instability.",
            "expected_concepts": ["Adaptive Beamforming", "spatial null steering", "sample covariance matrix", "MVDR Capon", "matrix inversion"],
            "sample_questions": [
                "Formulate the optimization problem for the Minimum Variance Distortionless Response (MVDR) adaptive beamformer and explain how it places spatial nulls on jammers.",
                "Why is direct sample covariance matrix inversion susceptible to numerical instability in finite-precision radar DSPs, and what regularization techniques (e.g. diagonal loading) are used?",
                "How does the computational complexity of adaptive beamforming scale with the number of antenna array channels M?"
            ],
            "rubric": {
                "poor": "Cannot explain spatial beamforming; thinks beamforming is done purely with analog phase shifters; unaware of covariance matrix.",
                "acceptable": "Explains that digital weights adjust phase and amplitude to point beams at targets and nulls at jammers; states MVDR formula.",
                "excellent": "Derives the MVDR weight vector using Lagrange multipliers, explains diagonal loading (R_xx + alpha*I) for robust beamforming, and details QR decomposition algorithms on systolic arrays."
            },
            "source": "Van-Trees-Optimum-Array-Processing",
            "source_title": "Optimum Array Processing: Part IV of Detection, Estimation, and Modulation Theory (Harry L. Van Trees)",
            "source_type": "textbook",
            "source_reference": "Van Trees, Chapter 6: Adaptive Beamformers"
        },
        {
            "id": "chunk_drdo_deep_rf_01",
            "role_id": "scientist_b_ece",
            "competency": "radar_rf_systems",
            "stage": "deep_dive",
            "difficulty_level": 4,
            "domain": "electronics_radar",
            "discipline": "Electronics & Communication Engineering",
            "topic": "Active Electronically Scanned Array (AESA) Radar Architectures",
            "title": "Active Electronically Scanned Array (AESA) Architecture, T/R Modules, and Beam Steering",
            "content": "Active Electronically Scanned Array (AESA) radars represent modern state-of-the-art radar technology, replacing passive mechanically rotated antennas with thousands of solid-state Transmit/Receive (T/R) modules distributed across the antenna aperture. Each individual T/R module incorporates a solid-state Power Amplifier (using Gallium Nitride - GaN or Gallium Arsenide - GaAs technology), a Low Noise Amplifier (LNA), digital phase shifters, variable attenuators, and circulators. Electronic beam steering without mechanical inertia enables instantaneous switching between target tracking, airspace surveillance, and missile guidance modes within microseconds. The progressive phase shift Delta_phi between adjacent antenna elements spaced at distance d to steer a beam to scan angle theta_0 is: Delta_phi = (2 * pi * d / lambda) * sin(theta_0). AESA provides graceful degradation: failure of a few individual T/R modules reduces ERP slightly without total radar mission failure.",
            "expected_concepts": ["AESA Beamforming", "transmit receive module", "GaN semiconductor", "electronic steering", "graceful degradation"],
            "sample_questions": [
                "Describe the hardware architecture of an AESA Transmit/Receive (T/R) module and explain how GaN technology has enhanced AESA performance.",
                "Derive the progressive phase shift formula required to electronically steer an AESA beam to an angle theta_0 off boresight.",
                "Why does an AESA radar exhibit superior operational availability ('graceful degradation') compared to traditional traveling-wave tube (TWT) transmitter systems?"
            ],
            "rubric": {
                "poor": "Cannot explain how electronic steering works without moving parts; unaware of T/R module internals.",
                "acceptable": "Draws block diagram of T/R module with PA, LNA, phase shifter, and switch; explains phase delta = (2*pi*d/lambda)*sin(theta).",
                "excellent": "Analyzes thermal dissipation in GaN vs GaAs, explains grating lobe avoidance (d <= lambda/(1 + |sin(theta_max)|)), and computes aperture gain loss under partial module failures."
            },
            "source": "Skolnik-Radar-Handbook",
            "source_title": "Radar Handbook (Merrill I. Skolnik)",
            "source_type": "reference",
            "source_reference": "Skolnik, 3rd Ed., Chapter 5: Phased Array Radar"
        },
        {
            "id": "chunk_drdo_deep_av_01",
            "role_id": "scientist_b_ece",
            "competency": "avionics_communication",
            "stage": "deep_dive",
            "difficulty_level": 4,
            "domain": "electronics_radar",
            "discipline": "Electronics & Communication Engineering",
            "topic": "Digital Modulation Schemes and Demodulation under Doppler Distortion",
            "title": "Digital Modulation Schemes (BPSK, QPSK, QAM) and Carrier Synchronization under Extreme Doppler Drift",
            "content": "Avionics telemetry, secure command links, and identification friend-or-foe (IFF) systems utilize digital phase shift keying (BPSK, QPSK, offset-QPSK) and Quadrature Amplitude Modulation (QAM). In high-speed airborne or missile platforms traveling at Mach velocities, the communication link suffers from massive Doppler frequency offsets and Doppler rate of change (f_d = v*f_c/c). Traditional phase-locked loops lose lock under severe Doppler step transients. Robust receiver architectures utilize Costas loops or decision-directed carrier tracking loops integrated with Fast Fourier Transform (FFT) coarse frequency acquisition engines to estimate and remove Doppler offsets prior to symbol demodulation and Viterbi / Low-Density Parity-Check (LDPC) forward error correction decoding.",
            "expected_concepts": ["Digital Modulation BPSK/QPSK", "Costas loop", "carrier synchronization", "Doppler drift tracking", "constellation diagrams"],
            "sample_questions": [
                "How does a Costas loop recover carrier phase in a suppressed-carrier BPSK or QPSK communication system?",
                "What effects does severe Doppler frequency shift have on received constellation points, and how is coarse Doppler estimation handled in airborne links?",
                "Compare QPSK and Offset-QPSK (OQPSK) in terms of envelope variation and spectral regrowth when passing through non-linear power amplifiers."
            ],
            "rubric": {
                "poor": "Cannot explain how phase shift keying is demodulated; unaware of Costas loop or carrier recovery.",
                "acceptable": "Explains that Costas loop multiplies I and Q branches to eliminate carrier ambiguity; notes that Doppler rotates constellation.",
                "excellent": "Derives the Costas error signal e = I*Q for BPSK, details OQPSK phase transition limitation to 90 degrees avoiding zero-crossings, and designs two-stage FFT + Costas tracking."
            },
            "source": "Proakis-Salehi-Digital-Communications",
            "source_title": "Digital Communications (John G. Proakis, Masoud Salehi)",
            "source_type": "textbook",
            "source_reference": "Proakis & Salehi, 5th Ed., Chapter 5: Carrier and Symbol Synchronization"
        },

        # --- Stage 6: Application / Scenario & System Engineering Design ---
        {
            "id": "chunk_drdo_app_01",
            "role_id": "scientist_b_ece",
            "competency": "radar_rf_systems",
            "stage": "application_scenario",
            "difficulty_level": 4,
            "domain": "electronics_radar",
            "discipline": "Electronics & Communication Engineering",
            "topic": "Scenario: High-Speed Target Tracking in Severe Ground and Sea Clutter",
            "title": "Radar System Scenario: Low-Altitude Target Tracking in High Clutter Environments",
            "content": "Engineering scenario evaluating applied radar design trade-offs: A sea-skimming anti-ship cruise missile is traveling at Mach 2 at 10 meters altitude over rough sea state 4. The naval radar must detect and establish track on this target amidst intense sea surface clutter (Rayleigh / K-distributed clutter) and multipath interference. The candidate must evaluate the selection of radar carrier frequency (X-band vs S-band), waveform parameters (high PRF vs medium PRF), Constant False Alarm Rate (CFAR) processor architecture (Cell-Averaging CFAR vs Order-Statistic CFAR), and Doppler filtering to maintain target tracking without swamping the tracking computer with false alarms.",
            "expected_concepts": ["constant false alarm rate", "clutter rejection", "multipath fading", "PRF selection", "Doppler filtering"],
            "sample_questions": [
                "In a scenario where a sea-skimming missile must be tracked over rough sea clutter, how would you configure the radar's CFAR detector and PRF to maximize detection probability while suppressing false alarms?",
                "Why does standard Cell-Averaging CFAR (CA-CFAR) suffer catastrophic detection loss in heterogeneous clutter edges or multi-target environments, and how does Order-Statistic CFAR (OS-CFAR) resolve this?",
                "How does multipath interference between the direct radar ray and the sea-surface reflected ray create deep signal nulls, and how can frequency agility mitigate it?"
            ],
            "rubric": {
                "poor": "Suggests simply raising detection threshold arbitrarily; unaware of CFAR algorithms or multipath effects.",
                "acceptable": "Explains that CFAR dynamically adjusts threshold based on surrounding noise cells; identifies OS-CFAR for multiple targets.",
                "excellent": "Analyzes K-distribution clutter statistics, compares CA-CFAR vs OS-CFAR windowing overhead, and designs pulse-to-pulse frequency agility to de-correlate sea multipath nulls."
            },
            "source": "Skolnik-Radar-Handbook",
            "source_title": "Radar Handbook (Merrill I. Skolnik)",
            "source_type": "reference",
            "source_reference": "Skolnik, 3rd Ed., Chapter 7: Automatic Detection, Tracking, and CFAR"
        },
        {
            "id": "chunk_drdo_app_02",
            "role_id": "scientist_b_ece",
            "competency": "avionics_communication",
            "stage": "application_scenario",
            "difficulty_level": 4,
            "domain": "electronics_radar",
            "discipline": "Electronics & Communication Engineering",
            "topic": "Scenario: EMI/EMC Shielding and High-Density Mixed-Signal PCB Design",
            "title": "Hardware Scenario: EMI/EMC Shielding, Grounding Planes, and Mixed-Signal PCB Isolation",
            "content": "Scenario evaluating electromagnetic compatibility in defence electronics: In a high-density radar digital receiver unit, high-speed digital processors (FPGA, DDR4 RAM clocked at GHz rates) co-exist on the same chassis as sensitive analog RF front-end circuitry (operating at microvolt signal levels). Candidate must explain how to pass stringent military EMC standards (such as MIL-STD-461G). Key design considerations include split vs continuous ground planes, return current loop minimization, differential trace impedance routing, bypass decoupling capacitor networks, optical/magnetic signal isolation, and chassis shielding gaskets to prevent radiated and conducted emissions from corrupting receiver sensitivity.",
            "expected_concepts": ["EMI/EMC Shielding", "ground plane return path", "MIL-STD-461G compliance", "decoupling capacitance", "chassis shielding"],
            "sample_questions": [
                "You are designing a mixed-signal PCB housing both a high-speed FPGA and a sensitive 16-bit radar ADC. How would you design the grounding architecture and return current paths to prevent digital switching noise from coupling into the analog ADC floor?",
                "Why is cutting or splitting the ground plane beneath high-speed digital traces a hazardous layout mistake that worsens radiated emissions?",
                "How do you design filtering on power input lines to pass MIL-STD-461G conducted emissions (CE102) requirements?"
            ],
            "rubric": {
                "poor": "Recommends cutting ground planes arbitrarily; unaware of return current loop inductance; cannot explain decoupling.",
                "acceptable": "Explains that high-frequency currents return directly beneath the signal trace; recommends continuous ground plane with spatial segregation of analog and digital zones.",
                "excellent": "Analyzes loop inductance V = L*(di/dt), details common-mode choke and feed-through capacitor selection for MIL-STD-461G, and designs Faraday shielding enclosures."
            },
            "source": "Ott-Electromagnetic-Compatibility",
            "source_title": "Electromagnetic Compatibility Engineering (Henry W. Ott)",
            "source_type": "textbook",
            "source_reference": "Ott, Chapters 3 & 10: Grounding and Mixed-Signal Layout"
        },
        {
            "id": "chunk_drdo_des_01",
            "role_id": "scientist_b_ece",
            "competency": "avionics_communication",
            "stage": "system_engineering_design",
            "difficulty_level": 4,
            "domain": "electronics_radar",
            "discipline": "Electronics & Communication Engineering",
            "topic": "System Engineering: Triple Modular Redundancy (TMR) and Majority Voting",
            "title": "System Engineering Design: Fault-Tolerant Triple Modular Redundancy (TMR) and Byzantine Voting",
            "content": "In mission-critical aerospace and defence computing (such as flight control computers or missile guidance units), hardware faults caused by component breakdown, cosmic radiation single-event upsets (SEU), or thermal stress must not compromise system operation. Triple Modular Redundancy (TMR) replicates critical computational modules into three identical parallel hardware channels (Module A, Module B, Module C) executing identical software synchronously. A hardware Majority Voter compares the outputs of all three channels; if two channels agree and one disagrees, the voter selects the matching output and logs a fault against the failing channel. Candidate must analyze single-point-of-failure vulnerabilities in the voter itself, clock synchronization across channels, and Byzantine fault handling when one channel outputs conflicting information to different voters.",
            "expected_concepts": ["Triple Modular Redundancy", "majority voter", "single event upset", "fault tolerance", "Byzantine agreement"],
            "sample_questions": [
                "Walk the board through the architectural design of a Triple Modular Redundant (TMR) computing system for a mission-critical missile guidance processor.",
                "How do you ensure that the hardware voter does not become a catastrophic single point of failure (SPOF) in a TMR design?",
                "How does a TMR architecture handle single-event upsets (SEUs) in FPGA configuration memory without requiring an operational reboot?"
            ],
            "rubric": {
                "poor": "Cannot explain TMR; unaware of voter single point of failure; confuses software retry with hardware redundancy.",
                "acceptable": "Explains three parallel processors with a 2-out-of-3 majority voting circuit; explains that single channel failure is masked.",
                "excellent": "Designs triplicated voters with independent clock synchronization, explains memory scrubbing for SEU recovery, and evaluates reliability curves where TMR exceeds simplex reliability."
            },
            "source": "Koren-Fault-Tolerant-Systems",
            "source_title": "Fault-Tolerant Systems (Israel Koren, C. Mani Krishna)",
            "source_type": "textbook",
            "source_reference": "Koren & Krishna, Chapter 3: Hardware Redundancy and Voting"
        },
        {
            "id": "chunk_drdo_des_02",
            "role_id": "scientist_b_ece",
            "competency": "techno_managerial",
            "stage": "system_engineering_design",
            "difficulty_level": 5,
            "domain": "electronics_radar",
            "discipline": "Electronics & Communication Engineering",
            "topic": "Safety-Critical DO-254 / DO-178C Airborne Systems Lifecycle Assurance",
            "title": "System Engineering Design: DO-254 Hardware and DO-178C Software Safety Assurance Lifecycles",
            "content": "Defence avionics systems deployed on aircraft must adhere to rigorous safety and design assurance standards: RTCA DO-254 for airborne electronic hardware (ASICs, FPGAs) and RTCA DO-178C for airborne software. Systems are classified into Design Assurance Levels (DAL A through DAL E) based on hazard severity resulting from failure (DAL A = Catastrophic: loss of aircraft/life; DAL B = Hazardous; DAL C = Major; DAL D = Minor; DAL E = No safety effect). High-criticality DAL A systems mandate comprehensive bi-directional traceability from high-level system requirements to low-level HDL code, tool qualification, worst-case timing analysis, and structural coverage metrics (Modified Condition/Decision Coverage - MC/DC) with independent verification.",
            "expected_concepts": ["DO-254 / DO-178C Guidelines", "design assurance levels", "bi-directional traceability", "MCDC coverage", "tool qualification"],
            "sample_questions": [
                "Explain the concept of Design Assurance Levels (DAL A through DAL E) under RTCA DO-254 / DO-178C standards and how they dictate development rigor.",
                "What is bi-directional requirement traceability, and why is it mandatory for safety-critical defence systems?",
                "What is Modified Condition/Decision Coverage (MC/DC), and why is standard branch coverage considered insufficient for DAL A software verification?"
            ],
            "rubric": {
                "poor": "Unaware of DO-254 or DO-178C; confuses standard commercial QA testing with formal aerospace design assurance.",
                "acceptable": "Outlines DAL A to E severity levels; explains traceability from requirements to code and test cases; explains that MC/DC tests every condition independently.",
                "excellent": "Demonstrates formal MC/DC test vector generation (N+1 tests per decision), explains independence requirements in verification teams, and details FPGA life-cycle artifacts for certification."
            },
            "source": "RTCA-DO-254-DO-178C",
            "source_title": "Design Assurance Guidance for Airborne Electronic Hardware & Software",
            "source_type": "official_standard",
            "source_reference": "RTCA DO-254 / EUROCAE ED-80 & RTCA DO-178C / EUROCAE ED-12C"
        },

        # --- Stage 7: Techno-Managerial ---
        {
            "id": "chunk_drdo_mgmt_01",
            "role_id": "scientist_b_ece",
            "competency": "techno_managerial",
            "stage": "techno_managerial",
            "difficulty_level": 4,
            "domain": "electronics_radar",
            "discipline": "Electronics & Communication Engineering",
            "topic": "Techno-Managerial: FMECA Risk Mitigation in Defence Projects",
            "title": "Techno-Managerial: Failure Modes, Effects, and Criticality Analysis (FMECA) in Defence Engineering",
            "content": "Techno-managerial governance in DRDO projects requires rigorous engineering risk management using Failure Modes, Effects, and Criticality Analysis (FMECA) per MIL-STD-1629A. Unlike generic management meetings, FMECA is a structured, quantitative engineering exercise: 1. Identify every component and subsystem failure mode. 2. Trace local effects up to full mission/system-level effects. 3. Quantify failure mode severity (Catastrophic, Critical, Marginal, Minor). 4. Evaluate failure probability/rate based on operational environmental stress. 5. Calculate the Criticality Number C_m and Risk Priority Number (RPN = Severity * Occurrence * Detection). 6. Engineer explicit fail-safe design mitigations (redundancy, watchdog reset, graceful degradation). A Scientist 'B' must lead technical risk discussions with cross-functional teams (software, hardware, thermal, mechanical) to resolve high-RPN failure modes before field qualification trials.",
            "expected_concepts": ["FMECA Risk Mitigation", "risk priority number", "single point of failure", "severity classification", "mitigation tracking"],
            "sample_questions": [
                "How is a Failure Modes, Effects, and Criticality Analysis (FMECA) conducted for a radar subsystem, and how do you calculate the Risk Priority Number (RPN)?",
                "If an analysis reveals a potential single point of failure (SPOF) with high severity in the radar power distribution unit, what technical and managerial steps do you take to resolve it?",
                "How do you prioritize limited engineering and testing resources when multiple subsystems present competing technical risks?"
            ],
            "rubric": {
                "poor": "Treats risk management as vague scheduling advice; unaware of FMECA methodology or RPN formula.",
                "acceptable": "Explains FMECA steps; calculates RPN = S * O * D; prioritizes failure modes with highest severity and likelihood.",
                "excellent": "Details MIL-STD-1629A criticality matrix, explains corrective action verification workflows, and integrates technical risk mitigation into defence milestone reviews (PDR/CDR)."
            },
            "source": "MIL-STD-1629A-FMECA",
            "source_title": "Procedures for Performing a Failure Mode, Effects and Criticality Analysis",
            "source_type": "official_standard",
            "source_reference": "MIL-STD-1629A, US Department of Defense Standard"
        },
        {
            "id": "chunk_drdo_mgmt_02",
            "role_id": "scientist_b_ece",
            "competency": "techno_managerial",
            "stage": "techno_managerial",
            "difficulty_level": 4,
            "domain": "electronics_radar",
            "discipline": "Electronics & Communication Engineering",
            "topic": "Techno-Managerial: MTBF Reliability Prediction and Obsolescence Management",
            "title": "Techno-Managerial: Mean Time Between Failures (MTBF) and Component Obsolescence Management",
            "content": "Defence electronic systems are engineered for operational lifespans spanning 15 to 30 years, operating in harsh thermal, vibration, and humidity environments. Reliability prediction using Mean Time Between Failures (MTBF) per MIL-HDBK-217F (Reliability Prediction of Electronic Equipment) evaluates component failure rates (lambda) under environmental stress factors (pi_T temperature factor, pi_Q quality factor, pi_E environment factor). Total system failure rate is the sum of component failure rates: lambda_sys = sum lambda_i, with MTBF = 1 / lambda_sys. Crucially, commercial off-the-shelf (COTS) semiconductor components face rapid obsolescence (3-5 year lifecycles). A technical lead must implement proactive Diminishing Manufacturing Sources and Material Shortages (DMSMS) obsolescence management: monitoring silicon roadmaps, designing modular pin-compatible FPGA abstractions, lifetime component buys, and second-sourcing to ensure defense readiness across multi-decade service.",
            "expected_concepts": ["MTBF Reliability Prediction", "Obsolescence Management", "MIL-HDBK-217F", "environmental stress factors", "second sourcing"],
            "sample_questions": [
                "Explain the mathematical relationship between component failure rates (lambda) and Mean Time Between Failures (MTBF) in electronic systems under MIL-HDBK-217F.",
                "How do you manage the risk of rapid semiconductor obsolescence (DMSMS) for an airborne radar system designed to operate in service for 20+ years?",
                "What trade-offs exist between using military-grade hermetic components vs screened Commercial Off-The-Shelf (COTS) components in defence avionics?"
            ],
            "rubric": {
                "poor": "Cannot define MTBF; unaware of component obsolescence issues in long-lifecycle defence programs.",
                "acceptable": "Explains MTBF = 1/lambda; describes environmental factors affecting failure; suggests buying spare chips or redesigning boards for obsolescence.",
                "excellent": "Calculates system failure rate using part stress method, designs modular IP-core FPGA architectures to insulate firmware from silicon obsolescence, and details DMSMS lifecycle management."
            },
            "source": "MIL-HDBK-217F-Reliability",
            "source_title": "Reliability Prediction of Electronic Equipment (DoD Handbook)",
            "source_type": "official_standard",
            "source_reference": "MIL-HDBK-217F Notice 2, Department of Defense, USA"
        }
    ]
    return chunks


def update_seed_knowledge():
    base_dir = Path(__file__).resolve().parent.parent
    kb_path = base_dir / "data" / "knowledge_base" / "seed_knowledge.json"
    
    if not kb_path.exists():
        raise FileNotFoundError(f"Seed knowledge not found at {kb_path}")
        
    with open(kb_path, "r", encoding="utf-8") as f:
        existing_chunks = json.load(f)
        
    print(f"Existing chunks: {len(existing_chunks)}")
    
    # 1. Tag existing software engineering chunks with domain = "cyber_computing"
    for c in existing_chunks:
        if "domain" not in c or not c["domain"]:
            c["domain"] = "cyber_computing"
        if "discipline" not in c or not c["discipline"]:
            c["discipline"] = "Computer Science & Engineering"
            
    # 2. Check which DRDO chunks are already present
    existing_ids = {c["id"] for c in existing_chunks}
    drdo_chunks = generate_drdo_chunks()
    
    added_count = 0
    updated_count = 0
    
    for dc in drdo_chunks:
        if dc["id"] in existing_ids:
            # Update existing
            for idx, c in enumerate(existing_chunks):
                if c["id"] == dc["id"]:
                    existing_chunks[idx] = dc
                    updated_count += 1
                    break
        else:
            existing_chunks.append(dc)
            added_count += 1
            
    print(f"Added {added_count} new DRDO chunks, updated {updated_count} chunks.")
    print(f"Total chunks in KB: {len(existing_chunks)}")
    
    # Verify domain distribution
    domains = {}
    for c in existing_chunks:
        d = c.get("domain", "unknown")
        domains[d] = domains.get(d, 0) + 1
    print(f"Domain distribution: {domains}")
    
    with open(kb_path, "w", encoding="utf-8") as f:
        json.dump(existing_chunks, f, indent=2, ensure_ascii=False)
        
    print(f"Successfully saved updated knowledge base to {kb_path}")


if __name__ == "__main__":
    update_seed_knowledge()
