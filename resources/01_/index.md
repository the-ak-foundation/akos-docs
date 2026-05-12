# Introduction

AKOS is a small embedded real-time operating system built for microcontrollers. It is organized around a priority-based scheduler and an
event-driven programming model, so application code can react to signals,
timers, and state changes instead of relying on one large super-loop.

## What AKOS Provides

- Memory management
- Preemptive task scheduling
- Software timers
- Inter-thread communication
- Inter-thread synchronization
- Hardware-dependent port layer for context switching and tick handling

## Supported Architectures

AKOS is primarily documented around the ARM Cortex-M family, where the current
port layer provides the core scheduler and context-switch integration. The
architecture split is kept deliberately small so additional targets can be
ported without changing the higher-level kernel model.

- **ARM Cortex-M3**

## Supported Compiler

The examples and build scripts in this repository are written for the GNU Arm
Embedded toolchain. The compiler support is kept intentionally focused so the
documented build and example flow stays consistent across the repo.

- **GNU Arm Embedded Toolchain**
