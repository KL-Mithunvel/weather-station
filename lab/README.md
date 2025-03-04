# Weather Data Acquisition and Analysis: Integrating DHT22 with Raspberry Pi & Statistical Modeling in R

## 1. Connecting DHT22 to Raspberry Pi

The **DHT22** sensor is used to measure temperature and humidity. Below is the pinout and connection to the Raspberry Pi 4 Model B:

| **DHT22 Pin** | **Raspberry Pi Pin** |
|--------------|--------------------|
| VCC (Power)  | 3.3V (Pin 1) or 5V (Pin 2) |
| Data         | GPIO4 (Pin 7) |
| Ground (GND) | GND (Pin 6) |

### Sample Python Code to Read DHT22 Data
the following code is just for demo for R lab.
```python
import adafruit_dht
import gpiozero
import board 
import time
cpu = gpiozero.CPUTemperature()
s = adafruit_dht.DHT22(board.D4)
while True:
	print(f'room temp: {s.temperature}oC, humidity: {s.humidity}%RH, cpu temp: {cpu.temperature}oC')
	time.sleep(1)
s.exit()

```
### Requireements:
```txt
Adafruit-Blinka==8.54.0
adafruit-circuitpython-busdevice==5.2.11
adafruit-circuitpython-connectionmanager==3.1.3
adafruit-circuitpython-dht==4.0.7
adafruit-circuitpython-requests==4.1.9
adafruit-circuitpython-typing==1.11.2
Adafruit-PlatformDetect==3.77.0
Adafruit-PureIO==1.1.11
binho-host-adapter==0.1.6
colorzero==2.0
gpiozero==2.0.1
pyftdi==0.56.0
pyserial==3.5
pyusb==1.3.1
rpi-ws281x==5.0.0
RPi.GPIO==0.7.1
sysv-ipc==1.1.0
typing_extensions==4.12.2
```
first 10 rows of EXCEL file:

![image](https://github.com/user-attachments/assets/f6c50799-f3fb-4ae9-a05f-f98cdbcfcb42)

- the file is also uploded.

---

## 2. Importing Data in R 

![image](https://github.com/user-attachments/assets/6ac719ba-3b9d-4058-8b66-05914795e90f)
![image](https://github.com/user-attachments/assets/123419b4-634f-4e21-92cd-571fb49229e3)


```r
data=weather_2025_02_18
summary(data)
plot(data$temp,type="l",main="Ambient temperature",xlab="sno",ylab="temp",col="blue")
plot(data$humidity,type="l",main="Ambient Humidity",xlab="sno",ylab="humidity",col="red")
plot(data$'cpu temp',type="l",main="CPU temperature",xlab="sno",ylab="cpu temp",col="yellow")
```
output:
![image](https://github.com/user-attachments/assets/91ce345e-7748-403f-a3f9-89c2fff58afe)

![image](https://github.com/user-attachments/assets/15244e63-7588-4070-b595-75f3c70bfd61)

![image](https://github.com/user-attachments/assets/b31d2d46-0d99-476f-b3ce-3a8cd09af11b)

![image](https://github.com/user-attachments/assets/6fc1e552-c52d-4d27-bfc3-284c01fd1eb0)

## 3. Correlation Analysis
```r
# Compute correlation matrix
correlation_matrix <- cor(weather_data[, c("temp", "humidity", "cpu_temp")])
print(correlation_matrix)

# Visualizing correlation using a heatmap
library(ggcorrplot)
ggcorrplot(correlation_matrix, lab = TRUE)
```

## 4. Regression Analysis (Two or More Variables)
### Simple Linear Regression
```r
# Predict CPU temperature based on atmospheric temperature
model1 <- lm(cpu_temp ~ temp, data=weather_data)
summary(model1)
```

### Multiple Linear Regression
```r
# Predict CPU temperature based on temperature and humidity
model2 <- lm(cpu_temp ~ temp + humidity, data=weather_data)
summary(model2)
```

## 5. Regression Visualization
```r
# Scatter plot with regression line
ggplot(weather_data, aes(x=temp, y=cpu_temp)) +
    geom_point() +
    geom_smooth(method="lm", col="blue") +
    labs(title="Regression of CPU Temp vs Atmospheric Temp", x="Temperature (°C)", y="CPU Temperature (°C)")
```

## 6. Model Diagnostics
```r
# Check Residuals
par(mfrow=c(2,2))
plot(model2)
```

## 7. Conclusion
- Correlation analysis helps understand the relationship between atmospheric temperature, humidity, and CPU temperature.
- Regression models allow us to predict CPU temperature based on environmental factors.
- Multiple regression improves prediction accuracy by including additional variables.

**This analysis provides insights into how weather conditions impact CPU temperature.**

---

## 8. GitHub Repository
[GitHub Repository Link](#) *https://github.com/KL-Mithunvel/weather-station*
