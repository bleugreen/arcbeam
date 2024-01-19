from gpiozero import PWMOutputDevice, OutputDevice
import time
import subprocess

# Set up the PWM device on GPIO 14 with an initial duty cycle of 0 (off)
fan_pwm = PWMOutputDevice(14, frequency=100, initial_value=0)

# Set up the GPIO pin for the transistor's base
fan_power = OutputDevice(4, initial_value=False)

def get_cpu_temperature():
    temp_str = subprocess.getoutput("vcgencmd measure_temp|sed 's/[^0-9.]//g'")
    return float(temp_str)

def calculate_fan_speed(temp, min_temp=50, max_temp=70, min_fan_speed=0.15):
    if temp < min_temp:
        return 0
    elif temp > max_temp:
        return 1
    else:
        return min_fan_speed + (1 - min_fan_speed) * (temp - min_temp) / (max_temp - min_temp)

try:
    while True:
        temp = get_cpu_temperature()
        fan_speed = calculate_fan_speed(temp)
        fan_pwm.value = fan_speed

        if fan_speed > 0:
            fan_power.on()  # Power the fan
        else:
            fan_power.off()  # Cut power to the fan

        time.sleep(5.0)

except KeyboardInterrupt:
    pass
finally:
    fan_pwm.close()  # Turn off PWM control
    fan_power.off()  # Cut power to the fan
