# Heart Failure Management System (Backend)

## Setup
1. Create python virtual environment
`python3 -m venv venv`
2. Activate virtual environment
`source venv/bin/activate`
3. Install library needed in requirements.txt
`pip install -r requirements.txt`

## Run Flask Server
1. Open terminal and type
    ```bash
        flask -app flaskr/webserver run
    ```
2. Hit API Endpoint with Web API Testing Client (Thunder Client, Postman API, etc.)
3. Get Prediction
   ```python
       json = {
           column1: value1,
           column2: value2, ...
       }
   
       requests.post('/predict/', data=json)
   ```
4. Get Recommendation
   ```python
       json = {
           column1: value1, # user existing lifestyle
           column2: value2, ...
           columnN: valueN # user characteristic
       }
   
       requests.post('/recommendation/', data=json)
   ```

   Will get the result of user recommended lifestyle with risk comparison with existing lifestyle. Here are one of response example
   ```json
   "lifestyle" : {
       "Column1": {
            "changeStatus": "True",
            "comparison": "<= 140.372 (-0.001-140.372)",
            "description": "Minutes outdoors 9am - 5pm not work day",
            "recommendedValueInterval": "(-0.001, 140.372]"
          },
       "ColumnN": {
            "changeStatus": "Status of change compared with existing user lifestyle",
            "comparison": "<= 140.372 (-0.001-140.372)",
            "description": "Lifestyle description",
            "recommendedValueInterval": "(pd.Interval]"
           }
   },
   "currentRisk": 99.98880624771118,
   "riskAfterRecommendation": 0.022367404017132,
   "riskReduction": 99.96643884369405,
   "timeGenerated": "2024-05-17",
   "timeTaken": "14.709s"
   "status": 200,
   "statusMessage": "Success retrieving recommendation data"
   ```

5. Get accepted data schema for JSON data by accessing both endpoint with GET HTTP Request method.