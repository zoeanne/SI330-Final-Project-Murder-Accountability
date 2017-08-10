from urllib.request import urlopen
import json
import csv
import plotly.plotly as py
import plotly.graph_objs as go


# Name: Zoe Halbeisen
# Unique name: zoeanne
# Course: SI 330 (final Project)
# Instructor: Matthew Kay
# 4/13/17


#######################################################################################################################

#This chunck of code allows my program to take user input. To do this I read in a text file of state codes (taken from Census Bureau site)
# because a user won't know that Michigan is say, code 26. So I take these codes and store into a dictionary as well as the abbreviations
#for states. These state codes are what are used in the API call.
state_codes_dict = {}
state_abrev_dict = {}
state_codes_file  = open('state_codes.txt', 'r')
for line in state_codes_file:
    line = line.split('|')
    state_codes_dict[line[2]] = line[0]
    state_abrev_dict[line[2]] = line[1]
# print(state_codes_dict)
# print(state_abrev_dict)

user_input = input('\nEnter state (must capitalize first letter, ex. Michigan): ')

#Here I put the selected state and store into variables that can be used throughout my program
try:
    state_code = state_codes_dict[user_input]
    state = ', ' + state_abrev_dict[user_input]
    UCR_state = user_input
    print('\n' + '****************************************' + '\n' +
          'Success! View the results for ' + UCR_state + ' in results.csv' + '\n' + 'Scatter plot will open in browser shortly.')
except:
    print('Error identifying state. Please restart the program and make sure to capitalize the first letter of the state.')


#######################################################################################################################


#This function uses urllib requests to get Small Area Income and Poverty Estimates (SAIPE) data from the Census Bureau API
#It uses the state_code and the API returns JSON. My function overall returns a nested dictionary which I store in the CB variable.
def census_bureau_SAIPE():
    cb_dict = {}
    with urlopen('http://api.census.gov/data/timeseries/poverty/saipe?'
                'get=NAME,SAEPOVRTALL_PT,SAEPOVALL_PT&for=county:*&in=state:'+state_code+'&time=2015'
                '&key=2e6011085a8ad8f429ba2fcfe3294f1b36eee61d') as response:
        str_response = response.read().decode('utf-8')
        obj = json.loads(str_response)
        for list in obj:
            cb_dict[list[0]] = {'pov_rate': list[1], 'pov_count': list[2]}
    return (cb_dict)


CB = census_bureau_SAIPE()
# print(CB)
# # print(len(CB)) #84 but really 83
# print(CB['Wayne County'])


######################################################################################################################


# all counties
# This function reads in data from the FBI Uniform Crime Reports (UCR). Looking specifically at UCR homicide data.
#The input is a file and a string representing the selected state. The output is a nested dictionary which I store in the UCR variable.
def read_ucr(filename, state):
    ucr_dict = {}
    with open(filename, 'rt', encoding='utf16') as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')
        for row in reader:
            if row['State'] == state:
                clearance = int(row['CLR'])
                murder = int(row['MRD'])
                if row['County'] not in ucr_dict:
                    ucr_dict[row['County']] = {'MRD': murder, 'CLR': clearance}
                else:
                    ucr_dict[row['County']]['MRD'] += murder
                    ucr_dict[row['County']]['CLR'] += clearance

    return (ucr_dict)


UCR = read_ucr('UCR_2015_ALL.csv', UCR_state)
# print(UCR)
# print(len(UCR)) #52
# print(UCR['Wayne, MI'])
# print('Clearance Rate:' , "{0:.2f}".format(UCR['Wayne, MI']['CLR']/UCR['Wayne, MI']['MRD']))


######################################################################################################################

#the following functions are for cleaning the data and to find matching counties that are in both data sets
def clean_CB(dict):
    counties = []
    for county in dict:
        a = county.split(' County')
        counties.append(a[0])
    return(counties)

def clean_UCR(dict):
    counties = []
    for county in dict:
        a = county.split(', ')
        counties.append(a[0])
    return(counties)



# print('\n')

# print(clean_CB(CB))
# print(clean_UCR(UCR))

#this is creating a list of matching counties in both datasets as well as counties with 5 or more homicides in 2015
match = []
no_match = []
for county in clean_CB(CB):
    if county in clean_UCR(UCR) and UCR[county + state]['MRD'] >= 5:
        match.append(county)
    else:
        no_match.append(county)
# print(match)
# print(no_match)


######################################################################################################################

#This function converts a float into a percentage
def convert_to_percentage(float):
    percentage = float*100
    formatted = "{0:.2f}".format(percentage)
    return formatted

#Writing out data to CSV file. I need the try and except for rare cases where CB data breaks its standard (see report for more details)
with open('results.csv', 'w', newline = '') as output_file:
    results_data_writer = csv.DictWriter(output_file,
                                         fieldnames = ['County', '# Homicides', '# Solved', 'Clearance Rate', 'Poverty Rate'],
                                         extrasaction = 'ignore',
                                         delimiter = ',', quotechar = '"')
    results_data_writer.writeheader()
    for county in match:
        try:
            results_data_writer.writerow({'County': county,
                                          '# Homicides': UCR[county + state]['MRD'],
                                          '# Solved': UCR[county + state]['CLR'],
                                          'Clearance Rate' : convert_to_percentage(UCR[county + state]['CLR']/UCR[county + state]['MRD']),
                                          'Poverty Rate': CB[county + ' County']['pov_rate']
                                          })
        except:
            results_data_writer.writerow({'County': county,
                                          '# Homicides': UCR[county + state]['MRD'],
                                          '# Solved': UCR[county + state]['CLR'],
                                          'Clearance Rate' : convert_to_percentage(UCR[county + state]['CLR']/UCR[county + state]['MRD']),
                                          'Poverty Rate': CB[county]['pov_rate']
                                          })

######################################################################################################################


# This chunk of code is creating a scatterplot of clearance vs poverty rates with Plotly.
# The scatterplot will open in the broswser.
x_clearance = []
y_poverty = []
for county in match:
    x_clearance.append(convert_to_percentage(UCR[county + state]['CLR'] / UCR[county + state]['MRD']))
    try:
        y_poverty.append(CB[county + ' County']['pov_rate'])
    except:
        y_poverty.append(CB[county]['pov_rate'])

trace = go.Scatter(
    x = x_clearance,
    y = y_poverty,
    mode = 'markers'
)
x_axis_template = dict(
    title = 'Clearance rate'
)
y_axis_template = dict(
    title = 'Poverty rate'
)
layout = go.Layout(
    title = '<b>Clearance Rates versus Poverty Rates in ' + UCR_state + '</b><br>(by county, units in percentages)',
    xaxis = x_axis_template,
    yaxis = y_axis_template,
)
data = [trace]
fig = go.Figure(
    data = data,
    layout = layout
)

py.plot(fig)