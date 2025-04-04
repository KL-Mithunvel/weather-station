data=weather_2025_02_18
summary(data)
plot(data$temp,type="l",main="Ambient temperature",xlab="sno",ylab="temp",col="blue")
plot(data$humidity,type="l",main="Ambient Humidity",xlab="sno",ylab="humidity",col="red")
plot(data$'cpu temp',type="l",main="CPU temperature",xlab="sno",ylab="cpu temp",col="yellow")

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

plot(data$temp, data$`cpu temp`)
regression1=lm(data$temp~data$`cpu temp`) 
regression1
abline(regression1) 

regression2=lm(data$`cpu temp`~data$temp) 
regression2
abline(regression2) 

standard_dev = sd(data$temp, na.rm = TRUE)
standard_dev

mean = mean(data$temp, na.rm = TRUE)
mean

z.test(x = data$temp, 
       mu = 25,            
       sigma.x = 2,       
       alternative = "two.sided", 
       conf.level = 0.95)

# Suppose 'weather_data' is your dataset, and 'humidity' is the column

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




# 1) Check sample means
mean_cpu   = mean(data$cpu_temp, na.rm = TRUE)
mean_out   = mean(data$temp, na.rm = TRUE)
cat("Mean CPU Temp:", mean_cpu, "\n")
cat("Mean Outdoor Temp:", mean_out, "\n")

# 2) Paired t-test
# Assuming each row in 'weather_data' is a simultaneous measurement.

paired_test = t.test(
  x = data$'cpu temp',
  y = data$temp,
  paired = TRUE,              # indicates matched pairs
  alternative = "two.sided",
  conf.level = 0.95
)

print(paired_test)
