# import library
import pandas as pd

import gspread as gs
from gspread_formatting import *

# clustering & visualization
from upsetplot import plot
import matplotlib.pyplot as plt

# read google spread sheet(core features)
gc = gs.service_account(filename='../secure-outpost-380004-8d45b1504f3e.json')

sheet = gc.open('CPU Feature Visualization').worksheet('simplized aws group(core)')
df = pd.DataFrame(sheet.get_all_records())
featureGroups = df['feature groups'].tolist()

df = df.drop('feature groups', axis=1)

values = []
for i in range(len(df)):
    values.append(df.iloc[i].tolist())

flagsToBinary = []
groupNumber = [str(i) for i in range(2,12)]

# flag bit를 & 연산하여 동일한 cpu flag를 가진 그룹을 추출.
for value in values:
    binary_string = ''.join(str(i) for i in value)
    binary_number = int(binary_string, 2)
    flagsToBinary.append(binary_number)

matrix = []
for binary in flagsToBinary:
    row = []
    for i in range(len(flagsToBinary)):
        if(binary & flagsToBinary[i] == binary):
            row.append(True)
        else:
            row.append(False)
    matrix.append(row)

transferable = pd.DataFrame(matrix, columns=groupNumber)
transferable.index = range(2, len(transferable)+2)
transferable = transferable.groupby(groupNumber).size()

plot(transferable, orientation='horizontal')
plt.show()

for i in range(len(matrix)):
    print(f'Transferable group{i+2} to ',end='')
    for j in range(len(matrix[i])):
        if(matrix[i][j]):
            print(j+2, end=', ')
    print()