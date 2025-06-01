# R Experiments Syntax Cheat Sheet

Below is a **concise syntax reference** (cheat sheet) covering key R commands from **Experiments 1 to 6**, based on the materials you’ve shared. You can use this as **study material** or a quick **syntax guide**.

---

## **Experiment 1: Introduction to R & Data Handling**
```r
# Creating a vector
x <- c(1, 2, 5)

# Arithmetic on vectors
a <- c(1, 3, 5, 7)
b <- c(2, 4, 6, 8)
a + b         # Addition
a - b         # Subtraction
5 * a         # Constant multiplication
a * b         # Element-wise product
a / b         # Element-wise division

# Converting numeric to character
as.character(5.2)

# Concatenating strings
paste("Baa", "Baa", "Black", "Sheep")

# Installing a package
install.packages("moments")

# Loading a package
library(moments)

# Importing a CSV file
my_data <- read.csv("myfile.csv", stringsAsFactors = FALSE)

# Viewing first few rows
head(my_data)

# Exporting data to CSV
write.csv(my_data, "output.csv", row.names = FALSE)
```

---

## **Experiment 2: Summary Statistics & Visualization**
```r
# Creating data frames
empid   <- c(1,2,3,4,5)
age     <- c(30,37,45,32,50)
gender  <- c("male","female","male","female","female")
status  <- c("staff","staff","faculty","faculty","staff")
empinfo <- data.frame(empid, age, gender, status)

# Summary statistics
summary(empinfo)

# Subsetting data
male   <- subset(empinfo, gender == "male")
female <- subset(empinfo, gender == "female")

# Tables (one-way & two-way)
table(empinfo$gender)
table(empinfo$gender, empinfo$status)

# Basic Plots
plot(empinfo$age, type = "l", main = "Age of employees", 
     xlab = "Index", ylab = "Age", col = "blue")

# Pie chart
pie(table(empinfo$gender))

# Bar plot
bar_data <- table(empinfo$gender, empinfo$status)
barplot(bar_data, beside = TRUE, xlim = c(1,15), ylim = c(0,5), 
        legend = rownames(bar_data), main = "Gender vs Status")

# Box plot
boxplot(empinfo$age ~ empinfo$status, col = c('red','blue'))
```

---

## **Experiment 3: Correlation & Simple Linear Regression**
```r
# Loading built-in dataset 'cars' (speed vs dist)
data <- cars

# Covariance & Correlation
cov(data$speed, data$dist)
cor(data$speed, data$dist)

# Correlation test
cor.test(data$speed, data$dist, method = "pearson")

# Simple Linear Regression
model1 <- lm(dist ~ speed, data = data)
summary(model1)

# Plot + Regression Line
plot(data$speed, data$dist)
abline(model1, col = "red")
```

---

## **Experiment 4: Multiple Linear Regression**
```r
# Multiple Linear Regression
# Suppose Y is the response; X1 and X2 are predictors
Y  <- c(110,80,70,120,150,90,70,120)
X1 <- c(30,40,20,50,60,40,20,60)
X2 <- c(11,10,7,15,19,12,8,14)

RegModel <- lm(Y ~ X1 + X2)
summary(RegModel)

# 3D Visualization (requires scatterplot3d)
install.packages("scatterplot3d")
library(scatterplot3d)

scatterplot3d(X1, X2, Y, main = "3D Plot")
scatterplot3d(X1, X2, Y)$plane3d(RegModel)
```

---

## **Experiment 5: Binomial Probability Distribution**
```r
# Binomial PMF (dbinom), CDF (pbinom), Quantiles (qbinom), Random (rbinom)

# Probability of exactly k successes in n trials (p = success probability)
dbinom(k, size = n, prob = p)

# Probability of at most k successes
pbinom(k, size = n, prob = p)

# Probability of at least k successes
1 - pbinom(k-1, size = n, prob = p)

# Quantiles
qbinom(0.1, size = 10, prob = 0.3)  # 10th percentile

# Generate random binomial variates
rbinom(8, size = 150, prob = 0.4)

# Example: n=4, p=0.02
n <- 4
p <- 0.02
dbinom(2, n, p)       # Exactly 2
pbinom(2, n, p)       # At most 2
1 - pbinom(1, n, p)   # At least 2
```

---

## **Experiment 6: Poisson & Normal Distributions**

### **Poisson Distribution**
```r
# Poisson parameter
lambda <- 4.5

# Probability of exactly x events
dpois(x, lambda)

# Probability of at most x events
ppois(x, lambda)

# Probability of at least x events
1 - ppois(x-1, lambda)

# Generating random Poisson variates
rpois(n, lambda)

# Example: lambda = m * p => 20 * 0.02 = 0.4
x_vals <- 0:20
px     <- dpois(x_vals, 0.4)
plot(x_vals, px, type = "h", main = "Poisson(0.4)")
```

### **Normal Distribution**
```r
# Probability density function: dnorm
# Cumulative distribution function: pnorm
# Quantile function: qnorm
# Random generation: rnorm

# PDF of N(mean=20, sd=5)
x <- seq(0, 40)
y <- dnorm(x, mean = 20, sd = 5)
plot(x, y, type = "l", main = "N(20,5^2)")

# Probability that X < 15
pnorm(15, mean = 20, sd = 5)

# Probability that X > 25
1 - pnorm(25, mean = 20, sd = 5)

# Probability that 15 < X < 25
pnorm(25, 20, 5) - pnorm(15, 20, 5)

# 85th percentile
qnorm(0.85, mean = 70, sd = 3)
```

---

## **Key Notes & Good Practices**
1. **Missing Data**: Always check for missing values (`NA`) before computation:
   ```r
   sum(is.na(my_data$column))
   ```
2. **Converting Data Types**: Use `as.numeric()`, `as.factor()`, etc., if needed.
3. **Packages**: Install once, load every session:
   ```r
   install.packages("ggplot2")
   library(ggplot2)
   ```
4. **Comments**: Use `#` to document important logic or steps.
5. **Help & Docs**: Use `?functionName` or `help(functionName)` to learn more about a function.

---

### **Conclusion**
This collection of **syntax** distills the **core R commands** from your six experiments, covering:

- **Data creation, import/export, and manipulation**  
- **Summary statistics, subsetting, and visualizations**  
- **Correlation, simple & multiple regression**  
- **Binomial, Poisson, and Normal distributions**

Use this **cheat sheet** as a quick reference while practicing or completing assignments. Happy coding!
