# ASCII Jellyfish

A bioluminescent ASCII jellyfish aquarium that runs directly in your terminal :D

![Animation Preview](assets/preview.gif)

## Features

- Procedurally generated ASCII jellyfish
- Natural bell contraction and tendril movement
- Dynamic bioluminescence and colored glow
- Simulated underwater currents and swimming momentum
- Collision avoidance between jellyfish
- Individual swimming rhythms and depth perception
- Reactive plankton and floating particles
- Automatic terminal resizing
- Optimized rendering for smooth animation
- No external Python dependencies for the animation

## Requirements

- Python 3
- A terminal supporting 24-bit RGB colors

A GPU-accelerated terminal is recommended for optimal performance.

## Usage

Download `jellyfish.py`, then run:

```bash
python jellyfish.py
```

Recommended configuration:

```bash
python jellyfish.py --count 6 --fps 60 --speed 0.7 --halo 1.5
```

## Customization

| Argument | Description |
|---|---|
| `--count` | Number of jellyfish |
| `--fps` | Target frame rate |
| `--speed` | Animation speed |
| `--halo` | Bioluminescence intensity |
| `--water-bg` | Background color in hexadecimal |
| `--seed` | Random generation seed |
| `--no-glow` | Disable glow effects |
| `--no-sync` | Disable synchronized rendering |

Press `Ctrl+C` to exit.

## Development History

| Version | Changes |
|---|---|
| V1–V4 | Initial animation, ASCII geometry, and anatomical refinement |
| V5–V6 | Dynamic bioluminescence and surrounding glow |
| V7–V11 | Natural bell contraction and synchronized tendril movement |
| V12–V13 | Swimming physics, water currents, depth, and collision avoidance |
| V14–V16 | Reactive plankton and underwater atmosphere |
| V17 | Rendering optimization and improved frame consistency |

## Inspiration

- [ASCII.rest Jellyfish](https://ascii.rest/jellyfish/)

## License

This project is available for personal, educational, and noncommercial use. Commercial use and resale are prohibited without prior written permission.
