import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import norm

df = pd.read_csv("mkt_data_top_500_traded_nasdaq.csv") #Read in data into a data frame
df = df[['symbol', 'date', 'close']]                   #Get new dataframe with only these columns

prices = df.pivot(index='date', columns='symbol', values='close')
prices.index = pd.to_datetime(prices.index)     #Convert string index to datetime 

#The problem is some assets will not have price data for all the dates over the last 5 years, 
#leading to NANs once pivoted
#Here we can choose to keep only assets that have price data all of dates over last 5 years
#Note: If we kept assets that had 100%< dates filled, then there would be irregular gaps in return calculations
#because the consecutive dates wouldn't all be evenly spread out
Universe = prices.columns[prices.notna().mean() == 1]  
prices = prices[Universe]

#Now get data frame with returns using the formula r(t) = (P(t) - P(t-1))/P(t-1)
#Because of this, the start date will be NANs because nothing comes before. So get rid with .dropna()
#First date/row is for 2020-8-18 and last is 2025-08-15
returns = prices.pct_change().dropna()

UniCovMat = returns.cov() #Covariance matrix of returns considering whole universe - i,j th entry is Cov(retruns of i,returns of j)

def PwithA(A,k):                                   #Generate a subset of tickets of size k that contains A
    U_minus_A = Universe[Universe != A]            #remove A from universe to sample from that set
    Samp_minus_A = np.random.choice(U_minus_A,size = k-1,replace=False) #This is where the sampling happens, but you sample k-1 elements
    return np.append(Samp_minus_A,A)               # add A back in and return final set

def SubCov_P(P):     #This gets the sub-covariance matrix from the universe-covariance matrix
    #applying .loc[A,B] gives columns of original df that are in A and rows that are in B. Then convert to numpy array
    return UniCovMat.loc[P,P].to_numpy()
    
def PRisk(P):    
    #This returns portfolio risk (variance of P) 
    #Arguement is list of assets
    #Only for equally weighted portfolios!
    
    #Each asset in portfolio P is weighted equally. 
    #w is the weight vector containing all the weights of each asset 
    numAssets = len(P)
    w = np.ones(numAssets) / numAssets
    CovP = SubCov_P(P) #Now get subcov matrix for P
    PRisk = np.sqrt(w@CovP@w)  #Now just use portfolio risk formula (standard deviation)
    return PRisk
    
def ExpectedSigmaA(A,k,numSims):          
    """
    Estimate expected value of portfolio risk for a portfolio of size k containing asset A via MC sim"
    Also gives uncertainty measures, i.e. SE and CI ----> Finish this part!
    """
    sigmaVals = [] #Place to store Prisk random samples
    
    for i in range(numSims):
        sigmaVals.append(PRisk(PwithA(A,k)))
    
    ESig = np.mean(sigmaVals)    #MC estimate of mean of each Prisk
    SE = np.std(sigmaVals,ddof = 1)/np.sqrt(numSims)  #standard error, where ddof= 1 to make it unbiased, because denominator is numSims - ddof
    
    return ESig, SE


def MRC_A(A,P):   
    """
     Gives the MRC for asset A in a portfolio P (Only for equally weighted portfolios!)
     Given the portfolio P and the weights of each asset w, can compute a vector
     containing all MRC values for each asset in P, where the ith entry is the MRC value for asset i
     Then we take the component corresponding to asset A
    """
    w = np.ones(len(P)) / len(P)
    RiskPort = np.sqrt(w@SubCov_P(P)@w)  #Just computes sigma_p (could also use PRisk function for this, but this is more efficient)
    MRCVec = (SubCov_P(P)@w)/RiskPort            #MRC vector 
    Aindex = np.where(np.asarray(P)==A)[0][0]    #np.asarray(P)==A creates a boolean mask where the only True is
                                                 #where the array value is A. np.where then gives us the index of 
                                                 #that true value
    return MRCVec[Aindex]

def ExpectedMRC_A(A,k,numSims): #Get the estimated expected value of MRC for asset A over portfolios of size k that contain A via Monte Carlo
    MRCVals = []                #Place to store sampled MRC vals 
    
    for i in range(numSims):
        P = PwithA(A,k)            #Sample a portfolio with A of size k
        MRCVals.append(MRC_A(A,P))  #Append the computed MRC val to list
    return np.mean(MRCVals) #Monte carlo estimate of mean

numSims = 100    #Every monte carlo sim will use this many simulations. Do at least 10,000
k = 5

#Gives a list of expected values of PRisk and MRC for each asset
E_PRisk = [ExpectedSigmaA(A,k,numSims) for A in Universe]    
E_MRC = [ExpectedMRC_A(A,k,numSims) for A in Universe] 

results_df = pd.DataFrame({
    'symbol': Universe,
    'E_sigma': E_PRisk,    # Expected portfolio vol for random EW portfolios of size k that include the asset
    'E_MRC': E_MRC,        # Expected marginal portfolio risk of the asset in those portfolios
}).sort_values('symbol').reset_index(drop=True)



"Doing the VaR stuff here"

def ReturnsForP(P, startD, endD):        
    """
    Takes list of tickers in portfolio P (equally weighted), start/end date as datetime,
    and returns the sub-DataFrame of total returns of P for each date in that period.
    """
    sub = returns.loc[startD:endD, P] #contains returns for each asset in ticker over time horizon 
    k = len(P)                        #Number of assets in P
    w = np.ones(k)/k                  #Weight vector
    return sub @ w 

def VaR_confidence(confidence, P, startD, endD):
    """
    Historical VaR at 'confidence' (e.g., 0.95) over [startD, endD].
    Returns percentage of portfolio value at risk (VaR_pct)
    """
    alpha = 1.0 - confidence                 
    rP = ReturnsForP(P, startD, endD).values #Gets only values in numpy array without dates 
    q_alpha = float(np.nanquantile(rP, alpha))
    VaR_pct = -q_alpha     
    return VaR_pct
