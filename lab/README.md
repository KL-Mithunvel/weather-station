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
### for full code refer GitHub Repository:
[GitHub Repository Link](#) *https://github.com/KL-Mithunvel/weather-station*

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
v1= var(data$temp, use = "complete.obs")
v1
v2=var(data$humidity, use = "complete.obs")
v2
v3=var(data$'cpu temp', use = "complete.obs")
v3

corr13=cor(data$temp, data$`cpu temp`, use = "complete.obs")
corr13

corr12=cor(data$temp, data$humidity, use = "complete.obs")
corr12

corr23=cor(data$humidity, data$'cpu temp', use = "complete.obs")
corr23
```
output:
![image](https://github.com/user-attachments/assets/a9faf631-5d50-4b31-86f8-af84afaf52a1)

## 4. Regression Analysis (Two or More Variables)
```r

data= weather_2025_02_18
data
#regression b/w temp, humidity and cpu temp
x=data$temp
x
y= data$humidity
y
z= data$`cpu temp`
z
r=lm(z~x+y)
r
summary(r)

library(scatterplot3d)
g=scatterplot3d(x,y,z)
g$plane(r)

```
output:
![image](https://github.com/user-attachments/assets/ac6f7537-6115-4873-b920-7a86146c55fe)
![image](https://github.com/user-attachments/assets/e66d5ec7-9ee2-4b97-ac1a-f50ecf7db4a6)

---
# 5. One-Sample z-Test Report
 Performing a One-Sample z-Test
This document demonstrates how to compute basic statistics and perform a **one-sample z-test** on a column of data in R.


```r
# Sample standard deviation of 'temp' (ignoring NA)
standard_dev = sd(data$temp, na.rm = TRUE)
standard_dev  # e.g. 3.621358

# Sample mean of 'temp' (ignoring NA)
mean_value = mean(data$temp, na.rm = TRUE)
mean_value  # e.g. 28.65497

z.test(
  x = data$temp,   # the sample data
  mu = 25,         # hypothesized mean
  sigma.x = 2,     # population standard deviation (assumed known)
  alternative = "two.sided",
  conf.level = 0.95
)
```
`na.rm = TRUE` ensures that missing values (`NA`) are ignored during computation.

### Understanding the Parameters
- **`x = data$temp`**: The sample data under test.
- **`mu = 25`**: The null hypothesis states that the true mean is 25.
- **`sigma.x = 2`**: The population standard deviation is assumed to be 2 (instead of using the sample’s 3.62).
- **`alternative = "two.sided"`**: Checks if mean ≠ 25.
- **`conf.level = 0.95`**: We want a 95% confidence interval.

### Output
![image](https://github.com/user-attachments/assets/362f8f07-eace-4548-b6a1-414fc9f11cf0)


#### Interpretation
1. **z = 67.814**: The test statistic is extremely large, indicating the sample mean is far from the hypothesized mean of 25.
2. **p-value < 2.2e-16**: Essentially zero, suggesting that observing a mean of ~28.65 (or more extreme) is virtually impossible under H₀.
3. **95% Confidence Interval**: [28.54934, 28.76061]. We’re 95% confident the true mean lies in this range.
4. **Sample estimate**: 28.65497, confirming the computed mean.

### Conclusion
- Since `p-value << 0.05`, we **reject** the null hypothesis that the true mean is 25.
- The data strongly suggests that the **true mean** of `temp` is around **28.65**—significantly higher than 25.

# Additional Hypothesis Testing Examples

This document provides two sample hypothesis tests you can run on your weather dataset:

1. **Hypothesis on Mean Humidity vs. Threshold**
2. **Comparing Indoor (CPU Temp) vs. Outdoor (temp) Variation**

---
## i. Hypothesis on Mean Humidity vs. Threshold

### Problem Statement
- **Null Hypothesis (H₀)**: The mean humidity is **50%** (or some chosen threshold).
- **Alternative Hypothesis (H₁)**: The mean humidity **≠ 50%**.

### Sample R Code
```r

# 1) Check the sample mean
mean_humidity = mean(data$humidity, na.rm = TRUE)
cat("Sample mean humidity:", mean_humidity, "\n")

# 2) Perform a one-sample t-test comparing mean humidity to 50%
# (You can also do a z-test if population SD is known)

test_result = t.test(
  x = data$humidity,
  mu = 50,              
  alternative = "two.sided",
  conf.level = 0.95
)

print(test_result)
```

### Explanation
1. **`mean(weather_data$humidity, na.rm = TRUE)`**: This finds your **sample mean**.
2. **`t.test(..., mu = 50)`**: Conducts a **one-sample t-test** to see if the true mean is different from 50.
3. **Interpretation**:
   - **p-value** < 0.05 ⇒ reject H₀ (humidity differs significantly from 50%).
   - **p-value** ≥ 0.05 ⇒ fail to reject H₀ (no evidence to say humidity differs from 50%).
4. **Confidence Interval**: Tells you the plausible range for the population mean humidity.

### output
![image](https://github.com/user-attachments/assets/f532371a-5251-44ac-8566-8ce508d762b4)

---
## ii. Compare Indoor (CPU Temp) vs. Outdoor (temp) Variation

### Problem Statement
- **Null Hypothesis (H₀)**: The mean CPU temperature = the mean outdoor temperature.
- **Alternative Hypothesis (H₁)**: The mean CPU temperature ≠ the mean outdoor temperature.

Often, these measurements can be viewed as "paired" if each CPU temp reading corresponds to the same timestamp as the outdoor temp reading.

### Sample R Code
```r
# 1) Check sample means
mean_cpu   <- mean(weather_data$cpu_temp, na.rm = TRUE)
mean_out   <- mean(weather_data$temp, na.rm = TRUE)
cat("Mean CPU Temp:", mean_cpu, "\n")
cat("Mean Outdoor Temp:", mean_out, "\n")

# 2) Paired t-test
# Assuming each row in 'weather_data' is a simultaneous measurement.

paired_test <- t.test(
  x = weather_data$cpu_temp,
  y = weather_data$temp,
  paired = TRUE,              # indicates matched pairs
  alternative = "two.sided",
  conf.level = 0.95
)

print(paired_test)
```
## output 
![image](https://github.com/user-attachments/assets/37b79103-ef8d-42fb-b1a4-0e00578d02e0)

### Explanation
1. **`t.test(..., paired = TRUE)`**: A **paired t-test** checks if two related measurements (CPU and outdoor temperatures) differ on average.
2. **p-value** < 0.05 ⇒ reject H₀ (there’s a significant difference between CPU temp and outdoor temp).
3. **p-value** ≥ 0.05 ⇒ fail to reject H₀ (no significant difference found).
4. You’ll also get a **95% confidence interval** for the mean difference (CPU temp – outdoor temp). If it excludes 0, it indicates a significant difference.

---

