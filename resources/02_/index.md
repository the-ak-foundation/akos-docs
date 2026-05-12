# Getting started

This page uses the [AK Embedded Base Kit for STM32L151](https://github.com/the-ak-foundation/ak-base-kit-stm32l151)
as the reference board.

That board is the best place to begin because it already matches the AKOS
target family, it ships with a board-specific boot/application memory map, and
it exposes a simple path for loading application firmware over USB.

## What The Board Gives You

The board README describes it as an evaluation kit for embedded learners. The
main features called out there are:

- STM32L151-based hardware
- 1.54 inch OLED LCD
- 3 push buttons
- 1 buzzer
- RS485, Qwiic Connect, and Grove expansion support

For AKOS documentation purposes, the most important part is that the kit is
already organized around a bootloader plus application split, which makes it a
good reference for how to place an RTOS application in flash.

## Flash Layout

The board repository documents this memory map:

- `0x08000000` for boot firmware
- `0x08002000` for shared BSF data
- `0x08003000` for the application image

That means an AKOS application for this board should not assume it starts at
the beginning of flash. The linker script and any flash programming workflow
need to respect the application start address at `0x08003000`.

## Recommended Setup

If you are bringing AKOS up on this board, the practical setup is:

1. Clone the AKOS source tree.
2. Enter the repository root.
3. Read the board README and schematic in the reference repository.
4. Use the AKOS example tree as the application template.
5. Build the example for STM32L151 with the GNU Arm Embedded Toolchain.
6. Adjust the linker script and flashing command to place the application at
   `0x08003000`.

Typical setup commands look like this:

```bash
git clone https://github.com/the-ak-foundation/akos.git
cd akos
cd examples/00-blink
make
```

The current AKOS blink example already shows the STM32L151 toolchain shape:

- `akos/examples/00-blink/Makefile`
- `akos/examples/00-blink/stm32l151xx.ld`
- `akos/examples/00-blink/startup_stm32l151xb.s`
- `akos/examples/00-blink/system_stm32l1xx.c`
- `akos/examples/00-blink/board.h`

Those files are the right place to adapt pin mapping, clock setup, and the
flash offset needed for this board.

## First Build

For a first pass, the normal workflow is:

```bash
cd akos/examples/00-blink
make
```

If you are targeting the AK Embedded Base Kit specifically, update the board
configuration so the final image is linked for the application region rather
than the boot region.

## Flashing The Board

The board README notes that once the boot and application images are loaded,
you can use `AK - Flash` to program the application directly over the USB port.

That makes the board useful in two stages:

- Load or update the boot image when you are working on low-level startup
- Flash the application image repeatedly while developing AKOS tasks

For AKOS development, the second path is the one you will use most often.

## What To Change First

When you port the example to this board, start with these items:

- `board.h` for LED, button, buzzer, and GPIO pin mappings
- `stm32l151xx.ld` for the application flash offset
- `system_stm32l1xx.c` for clock and oscillator setup
- `Makefile` for the final flash address and board-specific defines

## Result

After the board is configured correctly, the example should build and run on
the AK Embedded Base Kit with the expected LED activity.

\image html 02_result.gif "AKOS blinky example result"

## Next Steps

Once the board boots and the application image flashes correctly, continue to:

- [Kernel basics](../03_/index.md)
- [Threads management](../05_/index.md)
- [Scheduler](../06_/index.md)
- [Context switch](../07_/index.md)

From there you can start turning the board's buttons, display, and buzzer into
actual AKOS tasks and events.
