
## Introduction to R & Data Handling
- **Topics Covered**: Basic R commands, data types (numeric, character, logical, factor), creating vectors, performing arithmetic on vectors, reading and writing data.
- **Key Learning**: Familiarity with R environment, installing packages, reading CSV files, exporting results.
```r
# Creating vectors
my_vec <- c(1, 2, 5)

# Basic arithmetic
sum_vec <- sum(my_vec)
mult_vec <- 5 * my_vec

# Importing data
my_data <- read.csv("data.csv", stringsAsFactors = FALSE)

# Exporting data
write.csv(my_data, "output.csv", row.names = FALSE)
```
##  Summary Statistics & Visualization
- **Topics**: Creating data frames, summary statistics (mean, median, sd), frequency tables, bar plots, pie charts, box plots.
- **Key Learning**: Exploratory Data Analysis (EDA), subsetting data, factor levels.
```r
# Creating data frames
empid <- c(1,2,3,4,5)
age <- c(30,37,45,32,50)
empinfo <- data.frame(empid, age)

# Summary stats
summary(empinfo)

# Tables
table(empinfo$age)

# Basic plots
plot(empinfo$age, type="l")         # Line plot
pie(table(empinfo$empid))            # Pie chart
barplot(table(empinfo$age))          # Bar chart
boxplot(empinfo$age, main="Box Plot")# Box plot
```
##  Correlation & Simple Linear Regression
- **Topics**: Covariance, Pearson correlation, linear regression (`lm()`), interpreting the regression output.
- **Key Learning**: Relationship between variables, using built-in datasets like `cars`.
```r
# Covariance & correlation
cov(data$speed, data$dist)
cor(data$speed, data$dist)

# Simple linear regression
model <- lm(dist ~ speed, data=cars)
summary(model)

# Plot regression
plot(cars$speed, cars$dist)
abline(model, col="red")
```
##  Multiple Linear Regression
- **Topics**: Multiple predictors in regression, model interpretation, 3D plots using `scatterplot3d`.
- **Key Learning**: Extending the `lm()` function to `lm(Y ~ X1 + X2)`.
```r
# Example data
Y <- c(110,80,70)
X1 <- c(30,40,20)
X2 <- c(11,10,7)

# Multiple linear regression
RegModel <- lm(Y ~ X1 + X2)
summary(RegModel)

# 3D Visualization
install.packages("scatterplot3d")
library(scatterplot3d)
scatterplot3d(X1, X2, Y)
```
##  Binomial Probability Distribution
- **Topics**: `dbinom()`, `pbinom()`, `qbinom()`, `rbinom()`, binomial probability, at most/at least scenarios.
- **Key Learning**: Discrete distribution usage in R.
```r
n <- 4     # number of trials
p <- 0.02  # probability of success

# Exactly k successes
dbinom(k, size=n, prob=p)

# At most k successes
pbinom(k, size=n, prob=p)

# At least k successes
1 - pbinom(k-1, size=n, prob=p)

# Random binomial values
rbinom(10, size=4, prob=0.02)
```
##  Poisson & Normal Distributions
- **Topics**: Poisson distribution (`dpois()`, `ppois()`, etc.), normal distribution (`dnorm()`, `pnorm()`, etc.), visualizing distributions.
- **Key Learning**: Continuous vs discrete distributions, `plot()` for PMF/PDF.
```r
# Poisson example
lambda <- 0.4
x_vals <- 0:20
px <- dpois(x_vals, lambda)
plot(x_vals, px, type="h")

# Normal example
mean_val <- 20
sd_val   <- 5
x <- seq(0,40)
y <- dnorm(x, mean_val, sd_val)
plot(x, y, type="l")

# Probabilities
pnorm(15, mean=20, sd=5)   # P(X<15)
1 - pnorm(25, 20, 5)       # P(X>25)
```
## Hypothesis Testing for One-Sample Mean & Proportion
- **Topics**: One-sample z-tests (large sample, known σ), one-sample proportion tests, calculating p-values, acceptance/rejection of H₀.
- **Key Learning**: Large-sample approximations, usage of `qnorm()`, `pnorm()`, and manual formula.
```r
# One-sample z-test (mean)
xbar <- 14.6        # sample mean
mu0 <- 15.4         # hypothesized mean
sigma <- 2.5        # population SD
n <- 35             # sample size
z_val <- (xbar - mu0) / (sigma / sqrt(n))
p_val <- 2 * pnorm(z_val) # two-sided

# One-sample proportion test (manual)
n <- 640
x <- 63            # number of "successes"
p0 <- 0.1726       # hypothesized proportion
p_hat <- x/n
z_prop <- (p_hat - p0) / sqrt(p0*(1-p0)/n)
```

---
##  Hypothesis Testing for Two-Sample Means & Proportions
- **Topics**: Large-sample tests for difference of means, difference of proportions, critical values from `qnorm()`, concluding via p-value.
- **Key Learning**: Independent samples, combined proportion, test statistic formulas.
```r
# Two-sample mean test (z-test)
xbar1 <- 20; n1 <- 500
xbar2 <- 15; n2 <- 400
sigma <- 4  # assumed common population SD

z_val <- (xbar1 - xbar2) / (sigma * sqrt((1/n1) + (1/n2)))

# Two-sample proportion test
p1 <- 0.2; p2 <- 0.185
n1 <- 900; n2 <- 1600
P <- (n1*p1 + n2*p2)/(n1+n2)
Q <- 1 - P
z_prop <- (p1 - p2) / sqrt(P*Q*((1/n1)+(1/n2)))
```
##  t-Test (Independent, Paired) & F-Test
- **Topics**: t-tests for small samples (<30), Welch’s t-test for independent groups, paired t-test, F-test for comparing variances.
- **Key Learning**: `t.test()` usage with `paired=TRUE` or `paired=FALSE`, `var.test()` for F-test.
```r
# Two-sample t-test (independent)
sample1 <- c(19,17,15,21,16,18,16,14)
sample2 <- c(15,14,15,19,15,18,16,20)
result <- t.test(sample1, sample2) # Welch by default
print(result)

# Paired t-test
test1 <- c(19,17,15,21,16)
test2 <- c(15,14,15,19,15)
paired_res <- t.test(test1, test2, paired=TRUE)

# F-test
var_res <- var.test(sample1, sample2)
```
##  Chi-Square Goodness-of-Fit & Independence
- **Topics**: Pearson’s chi-square test, comparing observed vs. expected frequencies (goodness of fit), contingency tables (independence).
- **Key Learning**: Using `chisq.test()` for both single categorical variable (goodness of fit) and two categorical variables.
```r
# Goodness of fit
obs_freq <- c(5,35,75,84,45,12)
exp_freq <- dbinom(0:5, size=5, prob=0.5) * 256
chisq_stat <- sum((obs_freq - exp_freq)^2 / exp_freq)

# Chi-square test for contingency table
table_mat <- matrix(c(69,51,81,20,35,44), ncol=2, byrow=TRUE)
chisq_test <- chisq.test(table_mat)
chisq_test$p.value
```
##  ANOVA (CRD, RBD, LSD)
- **Topics**: One-way ANOVA (CRD), two-way ANOVA (RBD), Latin Square Design (3 factors but “lighter” than full 3-way ANOVA).
- **Key Learning**: Use `aov()` for analysis, interpret factor effects.
```r
# Completely Randomized Design
my_data <- data.frame(
  A=c(36,37,42,38,47),
  B=c(46,39,35,37,43),
  C=c(35,42,37,43,38)
)
st_data <- stack(my_data)
crd_res <- aov(values ~ ind, data=st_data)
summary(crd_res)

# Randomized Block Design
# Example with 3 states (columns) x 4 salesmen (rows)
# Reshaping data, then:
res_rbd <- aov(Sales ~ States + Salesmen)
summary(res_rbd)

# Latin Square Design
fit <- lm(freq ~ manure + cultivation + crop, data=lsd_data)
anova(fit)
```
## **Cheat Sheet & How to Use the Code**

### **1. Data Import & Export**
```r
read.csv("file.csv", stringsAsFactors=FALSE)
write.csv(data_frame, "output.csv", row.names=FALSE)
```
- **Use**: For reading/writing tabular data in CSV format.

### 2. Basic Summary & Plot
```r
summary(my_data)       # Gives min, max, mean, median, etc.
plot(x, y)             # Scatter/line plot depending on arguments
table(my_data$column)  # Frequency table
```
- **Use**: Quick EDA to understand the distribution.

### **3. Statistical Tests**

#### **3.1 t-test**
```r
t.test(x, y=NULL, paired=FALSE, alternative="two.sided", conf.level=0.95)
```
- **One-sample**: Provide `y=NULL` and `mu=some_value`.
- **Two-sample**: Provide `x` and `y`, with `paired=TRUE` if data is matched.

#### **3.2 z-test (Manual)**
```r
z_val <- (mean_x - mu0) / (sigma / sqrt(n))
p_val <- 2 * (1 - pnorm(abs(z_val)))
```
- **Use** if population SD (`sigma`) is known or n is large.

#### **3.3 Proportion z-test (Manual)**
```r
p_hat <- x/n
z_prop <- (p_hat - p0) / sqrt(p0*(1-p0)/n)
```

#### **3.4 ANOVA**
```r
model <- aov(response ~ factorA + factorB, data=my_data)
summary(model)
```
- **One-way**: Just one factor.
- **Two-way**: Two factors.
- **LSD**: 3 factors in a “Latin square” arrangement.

#### **3.5 Chi-Square**
```r
# Goodness of fit
chisq_val <- sum((obs - exp)^2 / exp)

# Contingency table
chisq.test(cont_table)
```

### **4. Visualization Tips**
- **Histogram**: `hist(my_data$column)`
- **Boxplot**: `boxplot(column ~ group, data=df)`
- **Scatterplot**: `plot(x, y, main="Title")`
- **Line Plot**: `plot(x, y, type="l")`

### **5. Common R Functions**
- **`mean(x)`**: Mean of x
- **`sd(x)`**: Standard deviation
- **`var(x)`**: Variance
- **`cor(x, y)`**: Correlation
- **`lm(formula, data=...)`**: Linear regression
- **`aov(formula, data=...)`**: ANOVA
- **`t.test()`**: T-tests
- **`chisq.test()`**: Chi-square tests
- **`pnorm(), qnorm(), dnorm(), rnorm()`**: Normal distribution functions
- **`dbinom(), pbinom(), qbinom(), rbinom()`**: Binomial distribution functions
- **`dpois(), ppois(), qpois(), rpois()`**: Poisson distribution functions
