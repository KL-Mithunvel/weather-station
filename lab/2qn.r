
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
