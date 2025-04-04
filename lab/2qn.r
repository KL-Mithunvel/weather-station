data= weather_2025_02_18
#regression b/w temp, humidity and cpu temp
x=data$temp

y= data$humidity
z= data$`cpu temp`
r=lm(z~x+y)
summary(r)

library(scatterplot3d)
g=scatterplot3d(x,y,z)
g$plane(r)
