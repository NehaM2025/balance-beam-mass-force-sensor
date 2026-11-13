# balance-beam API reference

Reference for the MicroPython firmware in [`src/main.py`](../src/main.py). It covers the configuration constants, the `AD7715` driver class, and the order in which the program runs. For wiring, setup, and how to use the scale, see the [README](../README.md).

## Contents

- [Hardware configuration](#hardware-configuration)
- [Configuration constants](#configuration-constants)
- [`AD7715` class](#ad7715-class)
- [Program flow](#program-flow)
- [Mass conversion](#mass-conversion)
- [Known limitations](#known-limitations)
- [Troubleshooting](#troubleshooting)

## Hardware configuration

| Signal | ESP32 GPIO | Direction |
|---|---|---|
| SPI clock (SCK) | 18 | Output |
| SPI MOSI | 23 | Output |
| SPI MISO | 19 | Input |
| AD7715 chip select (CS) | 5 | Output |
| AD7715 data ready (RDY) | 26 | Input, pull-up |
| AD7715 reset (RESET_BAR) | 27 | Output |
| INA125P sleep (SLEEP_BAR) | 25 | Output |
| Calibration button | 35 | Input |
| Measure button | 36 | Input |
| Red / green / blue LED | 16 / 13 / 4 | Output |

The AD7715 uses SPI bus 2 at 38,400 baud, polarity 1, phase 1, most significant bit first.

## Configuration constants

Defined at the top of `main.py`. Edit them before flashing.

| Name | Default | Meaning |
|---|---|---|
| `red_min`, `red_max` | 30.0, 250.0 | Mass range (g) that lights the red LED |
| `green_min`, `green_max` | 249.0, 600.0 | Mass range (g) that lights the green LED |
| `blue_min`, `blue_max` | 500.0, 1000.0 | Mass range (g) that lights the blue LED |
| `superWeight` | 1000 | Mass (g) of the full-scale calibration weight |
| `calZero` | 1 | Defined but not used by the current code |

The LED ranges are placeholders. The competition announces the real ranges during setup, and ranges may overlap, so more than one LED can light for the same mass.

## `AD7715` class

Driver for the Analog Devices AD7715 16-bit ADC over SPI. Creating an instance configures the SPI bus, resets the chip, and runs a self-calibration.

### Class constants

| Name | Value | Purpose |
|---|---|---|
| `WRITETO_SETUP` | `0b00010000` | Communications register: write to the setup register |
| `READFROM_DATA` | `0b00111000` | Communications register: read from the data register |
| `WRITETO_COMREG` | `0b00000000` | Communications register write |
| `NORMAL_MODE` | `0b00000110` | Setup register value for normal operation |
| `SELF_CALIB` | `0b01000110` | Setup register value that starts self-calibration |
| `ZERO_SCALE_CALIB` | `0b10000110` | Setup register value that starts zero-scale system calibration |
| `FULL_SCALE_CALIB` | `0b11000110` | Setup register value that starts full-scale system calibration |
| `CS_PIN` | `5` | Chip select GPIO |

### `AD7715()`

Creates the SPI bus, configures the RDY and CS pins, pulses the reset pin, writes the communications register, and calls `calibrate()`. Takes no arguments.

### `select()` and `deselect()`

Pull chip select low or high. The chip only listens to the bus while it is selected.

### `reset_spi()`

Writes four `0xFF` bytes to resynchronize the serial interface. The main program does not call it.

### `calibrate()`

Runs the ADC's internal self-calibration, waits for RDY to go low, reads the result, and prints it. Returns nothing.

### `zero_scale_system_calibrate()`

Runs system calibration at zero scale. Call it with the pan empty and the amplifier awake. It waits for RDY to go low, reads the result, and prints the value. Returns nothing.

### `full_scale_system_calibrate(weight)`

Runs system calibration at full scale. Call it with the full-scale weight on the pan and the amplifier awake.

| Parameter | Type | Description |
|---|---|---|
| `weight` | number | Calibration weight in grams. The current code accepts it but does not use it. |

Stores the raw 16-bit ADC value in `self.calFull`, which later measurements use as the 1000 g reference. Also prints the value.

### `read_adc()`

Waits for RDY to go low, reads the data register, and returns the reading.

| Returns | Type | Description |
|---|---|---|
| ADC reading | `int` | Unsigned 16-bit value from 0 to 65535 |

## Program flow

`main.py` runs as a script on boot:

1. Set up the buttons, LEDs, and amplifier sleep pin. The amplifier starts asleep.
2. Create the `AD7715` object, which self-calibrates.
3. Wait for the calibration button, then run zero-scale system calibration with the amplifier awake.
4. Wait for the calibration button again, then run full-scale system calibration and store `calFull`.
5. Loop forever:
   1. Wait for the measure button.
   2. Wake the amplifier, clear the LEDs, and wait for the reading to settle.
   3. Discard 5 warm-up readings, then average 25 readings.
   4. Convert to grams, print the average voltage and mass, and light the LEDs whose ranges contain the mass.
   5. Put the amplifier back to sleep.

## Mass conversion

```
average_adc = mean of 25 readings
voltage (V) = 1.859 x average_adc / calFull
mass (g)    = average_adc x (1000 / calFull)
```

The value 1.859 V is the measured sensor output at 1000 g. The printed mass uses one decimal place.

## Known limitations

- `read_adc()` and the calibration methods wait for RDY with no timeout, so the program hangs if the ADC never signals ready, for example when the chip is miswired.
- Only two calibration points are used (0 g and 1000 g), so error is largest at low mass.
- The firmware records zero readings in `zero_values` but does not yet use them to correct drift.
- `weight` in `full_scale_system_calibrate` and `calZero` are currently unused.

## Troubleshooting

| Symptom | What to check |
|---|---|
| Readings are always zero or always full scale | Check each stage of the signal chain separately: bridge voltage, amplifier output, ADC input, then the SPI wiring. Hardware and software faults look the same here. |
| Program stops after "running self calibration" | The ADC is not signaling ready. Check the RDY, reset, and crystal connections. |
| Readings drift or jump | Check the bypass capacitors and the shielded cable connection, and give the amplifier time to settle after waking. |
| Wrong LEDs light | Update the range constants at the top of `main.py` to match the ranges announced at setup. |
