Height = c(150, 152, 156, 158, 159,160, 161, 161, 163, 164,168, 170, 171, 173, 175,176, 178, 180, 181, 182,183, 185, 186, 188, 190)

Weight = c(50, 48, 55, 52, 57,60, 61, 61, 63, 64,68, 70, 72, 73, 75,76, 78, 80, 81, 82,84, 85, 86, 88, 90)

students_df = data.frame(Student_ID = 1:25,Height = Height,Weight = Weight)
students_df

mean_height = mean(students_df$Height)
mean_weight = mean(students_df$Weight)
mean_height
mean_weight

quartiles_height = quantile(students_df$Height)
quartiles_weight = quantile(students_df$Weight)
quartiles_height
quartiles_weight

mode_height =mfv(students_df$Height)
mode_weight = mfv(students_df$Weight)
mode_height
mode_weight

sd_height = sd(students_df$Height)
sd_weight = sd(students_df$Weight)
sd_height
sd_weight

plot(x = students_df$Height, y = students_df$Weight,main = "Scatter Plot: Height vs Weight",xlab = "Height (cm)",  ylab = "Weight (kg)")

plot(  students_df$Student_ID,  students_df$Weight,  type = "h",  main = "Bar-like Plot: Student Weights",  xlab = "Student ID",  ylab = "Weight (kg)")

density_height =density(students_df$Height)
plot(  density_height,  main = "Density Plot of Height",  xlab = "Height (cm)")

plot(x    = students_df$Student_ID,  y    = students_df$Weight,  type = "o",   main = "Line Plot: Student Weights",  xlab = "Student ID",  ylab = "Weight (kg)")

n=5
n
p=0.25
p
prob_3=dbinom(3,n,p)
prob_3
prob_fail=dbinom(0,n, p) + dbinom(1,n,p)
prob_fail
expected_correct = n * p
expected_correct 
x=0:n
px=dbinom(x,n,p)
cx= pbinom(x,n,p)
plot(x, px, type = "l", col = "blue",ylim = c(0, 1), main = "Binomial Probability & CDF", xlab = "Correct Answers", ylab = "Probability")
lines(x, cx, type = "l", col = "red")
legend("topleft", legend = c("PMF", "CDF"), col = c("blue", "red"), lty = c(1, 1), lwd = 2)

#(i) 
y = c(6.4, 15.05, 18.75, 30.25, 44.85, 48.94, 51.55, 61.5, 100.44, 111.42, 115.23, 120.54)
x1 = c(1.32, 2.69, 3.56, 4.41, 5.35, 6.2, 7.12, 8.87, 9.8, 10.65, 11.2, 12.51)
x2 = c(1.15, 3.4, 4.1, 8.75, 14.82, 15.15, 15.32, 18.18, 35.19, 40.4, 45.69, 50.87)
model=lm(y ~ x1 + x2)
summary(model)
coeff=coefficients(model)
coeff
scatterplot3d(y,x1,x2)
# (ii) Estimate cooking time for given values
new=data.frame(x1 = 15.8, x2 = 52.4)
predicted_y=predict(model, new)
predicted_y
# (iii) Visualize y values
scatterplot3d(x1, x2, y, color = "blue", main = "3D Scatter Plot of Cooking Time", xlab = "Oven Width (x1)", ylab = "Fuel Temperature (x2)", zlab = "Cooking Time (y)")


xbar=170
ybar=172
n1=6400
n2=1600
sd1=6.4
sd2=6.3
xbar
ybar
n1
n2
sd1
sd2
z=(xbar-ybar)/((sd1^2/n1)+(sd2^2/n2))^0.5
z
alpha=0.05
alpha
zalpha=qnorm(1-alpha)
zalpha
if(abs(z)<=zalpha){print("accept null hypothesis")}else{print("reject null hypothesis")}


heighest_temp=c(38.5,40.2,36.8,41.5,39.0,42.3,37.3,43.1,35.9,40.8)
heighest_temp
heighest_rain=c(170,185,160,200,175,210,155,220,145,190)
heighest_rain
#(a)
covariance=cov(heighest_temp,heighest_rain)
covariance
correlation=cor.test(heighest_temp,heighest_rain,method="pearson")
correlation
#(b)
correlation1=cor.test(heighest_temp,heighest_rain,method="spearman")
correlation1
