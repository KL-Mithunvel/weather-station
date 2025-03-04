data=weather_2025_02_18
summary(data)
plot(data$temp,type="l",main="Ambient temperature",xlab="sno",ylab="temp",col="blue")
plot(data$humidity,type="l",main="Ambient Humidity",xlab="sno",ylab="humidity",col="red")
plot(data$'cpu temp',type="l",main="CPU temperature",xlab="sno",ylab="cpu temp",col="yellow")
