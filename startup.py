import math
import board
import adafruit_dotstar as dotstar
import time
dots = dotstar.DotStar(board.SCK, board.MOSI, 64, brightness=0.1)

# Assuming you have a library to control the LED strip, like `dots`
# Initialize the LED strip here (if necessary)


def rainbow_color(pos):
    """
    Calculate a rainbow color based on the position.
    """
    return (int(127 * (1 + math.sin(pos + 0))),
            int(127 * (1 + math.sin(pos + 2 * math.pi / 3))),
            int(127 * (1 + math.sin(pos + 4 * math.pi / 3))))


def interpolate_color(color1, color2, factor):
    """
    Interpolate between two colors.
    """
    return tuple(int(a + (b - a) * factor) for a, b in zip(color1, color2))


# Animation parameters
num_leds = 64
animation_time = 6  # total animation time in seconds
steps = 64          # number of steps in the animation
pause_time = animation_time / steps  # time to pause between updates

# Bouncing White Pixel with Rainbow Pulse


for step in range(steps):
    ratio = float(step+1) / steps
    bounce_pos = int(ratio*num_leds)
    for i in range(bounce_pos):
        phase = (ratio) * 2 * math.pi
        dots[i] = rainbow_color(phase + ((i+1) / num_leds) * 2 * math.pi)

    time.sleep(pause_time / float(step+1))

for step in range(20):
    for i in range(num_leds):
        dots[i] = interpolate_color(dots[i], (0, 0, 0), step / 10)
    time.sleep(2/50.0)

# Turn off all LEDs at the end
for i in range(num_leds):
    dots[i] = (0, 0, 0)
