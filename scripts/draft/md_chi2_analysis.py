from time import sleep
import pandas as pd
import numpy as np
from scipy.spatial.distance import mahalanobis
from matplotlib import pyplot as plt
from scipy.stats import chi2, scoreatpercentile
from statsmodels.graphics.gofplots import qqplot

extent= 2
# leave out total 1% data from lower and higher tails
PERCENT_LOW=1
PERCENT_HIGH=99

# df= pd.read_csv(r'C:\Users\tashr\Documents\diag-cte\asegstats.csv')
# df= pd.read_csv(r'C:\Users\tashr\Documents\diag-cte\aparcstats_lh.csv')
df= pd.read_csv(r'C:\Users\tashr\Documents\diag-cte\aparcstats_rh.csv')
df = pd.DataFrame(df)
regions = df.columns.values[1:]
subjects = df[df.columns[0]].values
L = len(subjects)

columns = ['Subjects', 'Mahalonobis', 'Outlier']
md = pd.DataFrame(columns=columns)

X = df.values[ :,1:]
meanX = np.mean(X, axis=0)
ind = np.where(meanX == 0)
X = np.delete(X, ind, axis=1)


X = X/np.max(X, axis=0)
meanX = np.mean(X, axis=0)
covX = np.cov(X, rowvar=False)
icovX = np.linalg.inv(covX)
MD = np.zeros((L,))
for i in range(L):
    x = X[i,: ]
    # print(i)
    MD[i] = mahalanobis(x, meanX, icovX)
    # sleep(0.5)

# print(MD)
d2= MD**2

measure= MD
print('\nOutliers based on MD percentiles')
h_thresh = scoreatpercentile(measure, PERCENT_HIGH)
l_thresh = scoreatpercentile(measure, PERCENT_LOW)
inliers = np.logical_and(measure <= h_thresh, measure >= l_thresh)

print(subjects[~inliers])

print('Outliers based on Chi2 probability')
lt= chi2.ppf(PERCENT_LOW/100, X.shape[1])
ht= chi2.ppf(PERCENT_HIGH/100, X.shape[1])
ind= np.logical_or(d2<lt, d2>ht)
print(subjects[ind])

# observed probabilities/percentiles
 # np.sort(MD**2)
# po, bins= np.histogram(d2, bins=round(L*0.10), density=True)
po= np.percentile(d2,range(100))

# expected probabilities.percentiles
# pe= chi2.pdf(bins, X.shape[1])
pe= chi2.ppf(np.arange(0,1,0.01), X.shape[1])

# print('Observed: ', np.round(po,4))
# print('Expected: ', np.round(pe,4))

# q-q/p-p plot
plt.figure()
plt.grid()
plt.xlabel('Expected')
plt.ylabel('Observed')
plt.title('P-P plot of squared Mahalanobis distance')
# plt.plot(pe[:-1], po, 'r-')
plt.plot(pe, po, 'r-')
plt.plot([0,99], [0,99])
plt.show(block= False)

# q-q plot by statsmodels
# fig= plt.figure()
# ax= fig.gca()
# ax.grid()
# qqplot(d2, line='r', dist= chi2(X.shape[1]), ax=ax)
# plt.show(block=False)


plt.figure()
plt.grid()
plt.xlabel('MD^2')
plt.ylabel('Histogram')
plt.hist(d2, bins=round(L*0.10))
plt.show(block=False)



pchi2= chi2.pdf(d2, X.shape[1])
plt.figure()
plt.grid()
plt.xlabel('MD^2')
plt.ylabel('Chi2 prob')
ind= np.argsort(d2)
# print(np.round(p[ind],4))
plt.plot(d2[ind], pchi2[ind], 'r-')
plt.show()




