# Correlation and Regression Analysis in R

## 1. Importing Data
```r
# Load necessary libraries
library(ggplot2)

# Read the CSV file (Ensure the correct path is provided)
weather_data <- read.csv("weather_data.csv", stringsAsFactors = FALSE)

# Convert time_stamp to Date-Time format
weather_data$time_stamp <- as.POSIXct(weather_data$time_stamp, format="%Y-%m-%d %H:%M:%S")

# Display first few rows
head(weather_data)
```

## 2. Correlation Analysis
```r
# Compute correlation matrix
correlation_matrix <- cor(weather_data[, c("temp", "humidity", "cpu_temp")])
print(correlation_matrix)

# Visualizing correlation using a heatmap
library(ggcorrplot)
ggcorrplot(correlation_matrix, lab = TRUE)
```

## 3. Regression Analysis (Two or More Variables)
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

## 4. Regression Visualization
```r
# Scatter plot with regression line
ggplot(weather_data, aes(x=temp, y=cpu_temp)) +
    geom_point() +
    geom_smooth(method="lm", col="blue") +
    labs(title="Regression of CPU Temp vs Atmospheric Temp", x="Temperature (°C)", y="CPU Temperature (°C)")
```

## 5. Model Diagnostics
```r
# Check Residuals
par(mfrow=c(2,2))
plot(model2)
```

## Conclusion
- Correlation analysis helps understand the relationship between atmospheric temperature, humidity, and CPU temperature.
- Regression models allow us to predict CPU temperature based on environmental factors.
- Multiple regression improves prediction accuracy by including additional variables.

**This analysis provides insights into how weather conditions impact CPU temperature.**

