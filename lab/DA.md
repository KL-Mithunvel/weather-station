# DIGITAL ASSISTANT-1
## 23BMH1029    Mithunvel K.L
### 1)	Prepare a dataset with height and weight of25 students in your class. Find the mean, quartiles, mode and SD of the data. Also, visualize the data using 4 different plots.  
```r
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
```
OUTPUT:
```r
> Height = c(150, 152, 156, 158, 159,160, 161, 161, 163, 164,168, 170, 171, 173, 175,176, 178, 180, 181, 182,183, 185, 186, 188, 190)
> 
> Weight = c(50, 48, 55, 52, 57,60, 61, 61, 63, 64,68, 70, 72, 73, 75,76, 78, 80, 81, 82,84, 85, 86, 88, 90)
> 
> students_df = data.frame(Student_ID = 1:25,Height = Height,Weight = Weight)
> students_df
   Student_ID Height Weight
1           1    150     50
2           2    152     48
3           3    156     55
4           4    158     52
5           5    159     57
6           6    160     60
7           7    161     61
8           8    161     61
9           9    163     63
10         10    164     64
11         11    168     68
12         12    170     70
13         13    171     72
14         14    173     73
15         15    175     75
16         16    176     76
17         17    178     78
18         18    180     80
19         19    181     81
20         20    182     82
21         21    183     84
22         22    185     85
23         23    186     86
24         24    188     88
25         25    190     90
> 
> mean_height = mean(students_df$Height)
> mean_weight = mean(students_df$Weight)
> mean_height
[1] 170.8
> mean_weight
[1] 70.36
> 
> quartiles_height = quantile(students_df$Height)
> quartiles_weight = quantile(students_df$Weight)
> quartiles_height
  0%  25%  50%  75% 100% 
 150  161  171  181  190 
> quartiles_weight
  0%  25%  50%  75% 100% 
  48   61   72   81   90 
> 
> mode_height =mfv(students_df$Height)
> mode_weight = mfv(students_df$Weight)
> mode_height
[1] 161
> mode_weight
[1] 61
> 
> sd_height = sd(students_df$Height)
> sd_weight = sd(students_df$Weight)
> sd_height
[1] 11.89187
> sd_weight
[1] 12.67175
> 
> plot(x = students_df$Height, y = students_df$Weight,main = "Scatter Plot: Height vs Weight",xlab = "Height (cm)",  ylab = "Weight (kg)")
> 
> plot(  students_df$Student_ID,  students_df$Weight,  type = "h",  main = "Bar-like Plot: Student Weights",  xlab = "Student ID",  ylab = "Weight (kg)")
> 
> density_height =density(students_df$Height)
> plot(  density_height,  main = "Density Plot of Height",  xlab = "Height (cm)")
> 
> plot(x    = students_df$Student_ID,  y    = students_df$Weight,  type = "o",   main = "Line Plot: Student Weights",  xlab = "Student ID",  ylab = "Weight (kg)")
> 
```
![image](https://github.com/user-attachments/assets/530e178a-9bc8-4cd9-aa6f-e085485183b5)
![image](https://github.com/user-attachments/assets/567b18f0-96f5-4c7f-a50c-52dccfb5bea3)
![image](https://github.com/user-attachments/assets/819c6e30-b115-4d8e-804b-55b7efc3011d)
![image](https://github.com/user-attachments/assets/0d9862ab-eeaa-4cf4-8ddd-678295a2a677)


### 2)	A student takes a 5-question multiple-choice quiz, where each question has 4 answer choices (one correct). Thus, the probability of correctly guessing any question is 0.25. 
### (i) Find the probability that the student answers exactly 3 questions correctly. 
### (ii) Find the probability that the student fails the quiz. 
### (iii) Compute the expected number of correct answers. 
### (iv) Plot the probability density and cumulative distribution functions of the binomial probability distribution in the same figure.             
```r
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
```
OUTPUT:
```r
> n=5
> n
[1] 5
> p=0.25
> p
[1] 0.25
> prob_3=dbinom(3,n,p)
> prob_3
[1] 0.08789063
> prob_fail=dbinom(0,n, p) + dbinom(1,n,p)
> prob_fail
[1] 0.6328125
> expected_correct = n * p
> expected_correct 
[1] 1.25
> x=0:n
> px=dbinom(x,n,p)
> cx= pbinom(x,n,p)
> plot(x, px, type = "l", col = "blue",ylim = c(0, 1), main = "Binomial Probability & CDF", xlab = "Correct Answers", ylab = "Probability")
> lines(x, cx, type = "l", col = "red")
> legend("topleft", legend = c("PMF", "CDF"), col = c("blue", "red"), lty = c(1, 1), lwd = 2)
> 
```
![image](https://github.com/user-attachments/assets/10159fa2-6abe-47d1-9738-588a04646bb1)
                                 
### 3) A set of experimental runs was made to determine a way of predicting cooking time 𝑦 at various values of oven width 𝑥1 and fuel temperature 𝑥2. The coded data were recorded as follows:
![image](https://github.com/user-attachments/assets/e936bbac-8d98-43e4-8103-02621bc325d6)
### (i) Fit a multiple linear regression equation of the form y=b_0+b_1 x_1+b_2 x_2 and plot the model. 
### (ii) Estimate the cooking time when the oven width is 15.8 and fuel temperature is 52.4. 
### (iii) Plot the given data by visualizing 𝑦. 

 
```r
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

```
OUTPUT:
```r
> #(i) 
> y = c(6.4, 15.05, 18.75, 30.25, 44.85, 48.94, 51.55, 61.5, 100.44, 111.42, 115.23, 120.54)
> x1 = c(1.32, 2.69, 3.56, 4.41, 5.35, 6.2, 7.12, 8.87, 9.8, 10.65, 11.2, 12.51)
> x2 = c(1.15, 3.4, 4.1, 8.75, 14.82, 15.15, 15.32, 18.18, 35.19, 40.4, 45.69, 50.87)
> model=lm(y ~ x1 + x2)
> summary(model)

Call:
lm(formula = y ~ x1 + x2)

Residuals:
    Min      1Q  Median      3Q     Max 
-8.5292 -0.9287 -0.5306  0.7280  6.7223 

Coefficients:
            Estimate Std. Error t value Pr(>|t|)    
(Intercept) -0.03026    3.91216  -0.008 0.993997    
x1           3.87570    1.22264   3.170 0.011367 *  
x2           1.58471    0.25543   6.204 0.000158 ***
---
Signif. codes:  0 ‘***’ 0.001 ‘**’ 0.01 ‘*’ 0.05 ‘.’ 0.1 ‘ ’ 1

Residual standard error: 4.266 on 9 degrees of freedom
Multiple R-squared:  0.9913,	Adjusted R-squared:  0.9894 
F-statistic: 514.8 on 2 and 9 DF,  p-value: 5.25e-10

> coeff=coefficients(model)
> coeff
(Intercept)          x1          x2 
-0.03026021  3.87569982  1.58471489 
> scatterplot3d(y,x1,x2)
> # (ii) Estimate cooking time for given values
> new=data.frame(x1 = 15.8, x2 = 52.4)
> predicted_y=predict(model, new)
> predicted_y
       1 
144.2449 
> # (iii) Visualize y values
> scatterplot3d(x1, x2, y, color = "blue", main = "3D Scatter Plot of Cooking Time", xlab = "Oven Width (x1)", ylab = "Fuel Temperature (x2)", zlab = "Cooking Time (y)")
> 
```
![image](https://github.com/user-attachments/assets/a100b711-d451-4fde-99f3-07948eb4336e)

### 4)	A sample of heights of 6400 Englishmen has a mean of 170 cm and a standard deviation of 6.4 cm, while a sample of heights of 1600 Australians has a mean of 172 cm and a standard deviation of 6.3 cm. Do the data indicate that the Australians are on the average taller than the Englishmen?

```r
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
```
OUTPUT:
```r
> xbar=170
> ybar=172
> n1=6400
> n2=1600
> sd1=6.4
> sd2=6.3
> xbar
[1] 170
> ybar
[1] 172
> n1
[1] 6400
> n2
[1] 1600
> sd1
[1] 6.4
> sd2
[1] 6.3
> z=(xbar-ybar)/((sd1^2/n1)+(sd2^2/n2))^0.5
> z
[1] -11.32164
> alpha=0.05
> alpha
[1] 0.05
> zalpha=qnorm(1-alpha)
> zalpha
[1] 1.644854
> if(abs(z)<=zalpha){print("accept null hypothesis")}else{print("reject null hypothesis")}
[1] "reject null hypothesis"
```

### 5)	(a) Compute the covariance between the highest temperature and highest rainfall, and then determine the correlation coefficient between these two variables using Pearson’s formula. 	
### (b) Perform a Spearman’s correlation test to check for an association between temperature and rainfall.                                                                                                                 
![image](https://github.com/user-attachments/assets/4bb8b355-abbc-4fcf-86db-b55d46784665)

```r
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

```
OUTPUT:
```r
> heighest_temp=c(38.5,40.2,36.8,41.5,39.0,42.3,37.3,43.1,35.9,40.8)
> heighest_temp
 [1] 38.5 40.2 36.8 41.5 39.0 42.3 37.3 43.1 35.9 40.8
> heighest_rain=c(170,185,160,200,175,210,155,220,145,190)
> heighest_rain
 [1] 170 185 160 200 175 210 155 220 145 190
> #(a)
> covariance=cov(heighest_temp,heighest_rain)
> covariance
[1] 59.06667
> correlation=cor.test(heighest_temp,heighest_rain,method="pearson")
> correlation

	Pearson's product-moment correlation

data:  heighest_temp and heighest_rain
t = 21.909, df = 8, p-value = 1.988e-08
alternative hypothesis: true correlation is not equal to 0
95 percent confidence interval:
 0.9642853 0.9981234
sample estimates:
      cor 
0.9917694 

> #(b)
> correlation1=cor.test(heighest_temp,heighest_rain,method="spearman")
> correlation1

	Spearman's rank correlation rho

data:  heighest_temp and heighest_rain
S = 2, p-value < 2.2e-16
alternative hypothesis: true rho is not equal to 0
sample estimates:
      rho 
0.9878788 

> 
```
