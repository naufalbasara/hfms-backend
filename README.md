# Lifestyle Recommendation System for Heart Failure Patient

Lifestyle recommendation system that generate optimal lifestyle for personalized heart failure patients using given characteristics data (e.g. age, body metrics, blood pressure, etc.) and existing lifestyle (e.g. sleep duration, diet, and physical activities) to reduce the severity of the disease.

## Why

Cardiovascular disease is a group of disorders of the heart and blood vessels. One of the most common heart diseases is coronary heart disease. From the long and expensive medical procedures for patients, at least 50% of heart disease patients require readmission or re-hospitalization. The readmission rate is influenced by several factors, one of which is lifestyle. The focus of this project aims to develop a system that can predict the risk of heart disease and provide optimal lifestyle recommendations to minimize the severity of heart disease. The algorithm used in this study is long short-term memory (LSTM) as a model to predict the risk of heart disease. In addition, genetic algorithms are used as optimization models to determine the recommended lifestyle. These lifestyle recommendations are evaluated based on the results of heart disease risk predictions and take the lifestyle with the lowest risk using an optimization model.

![Representasi Kromosom (2)](https://github.com/user-attachments/assets/6c4eaa13-154f-4636-ab7c-cf4eb4da07b2)
Recommendation system overview, 2024

## Quick Start

Starting the project either with python or docker.

### Starting with Python

When starting with Python, you have to ensure the local libraries required in this project already installed. Required libraries are listed in `requirements.txt` file.

1. Python development server
```bash
flask --app webserver run
```

2. Python production server
```bash
gunicorn -b :8080 --timeout 360 --chdir /flaskr webserver:app
```

### Starting with Docker

Pull the latest build project's image on docker hub. See the full list of deployment in [docker hub](https://hub.docker.com/repository/docker/naufalbasara/hfms-backend/general).

```bash
# pull the image with specified tag name
docker pull naufalbasara/hfms-backend:deployment-appv4

# run the pulled image in port 8080
docker run -it -d naufalbasara/hfms-backend:deployment-appv4 -p :8080
```

## Usage

1. Once the server is running, the project will be accessible at http://localhost:8080 or http://0.0.0.0:8080.
2. Getting the prediction of heart failure risk from particular individual's by requesting the HTTP POST Request to http://localhost:8080/v3/predictions/

   Request Payload Example:
   ```json
   {
   "Column1": 110, "Column2": 9, "Column3": 1402, "Column4": 92, "ColumnN": 42
   }
   ```
   
   Response Payload Example:
   ```json
   {
      "probability": "25.857403874397278",
      "result": {
        "label": "0",
        "text": "Not having heart failure."
      },
      "status": 200,
      "timeGenerated": "2024-10-04",
      "timeTaken": "0.42859506607055664 s"
   }
   ```

4. Getting the lifestyle recommendation of heart failure risk from particular individual's by requesting the HTTP POST Request to http://localhost:8080/v3/recommendations/

   Request Payload Example:
   ```json
   {
   "Column1": 110, "Column2": 9, "Column3": 1402, "Column4": 92, "ColumnN": 42
   }
   ```
   
   Response Payload Example:
   ```json
   "lifestyle" : {
       "Column1": {
            "changeStatus": "False",
            "codeValue": "3",
            "comparison": "Tidak ada perubahan",
            "currentValue": "(1094.0, 6495.0]",
            "description": "Calcium (Mg)",
            "recommendedValueInterval": "Tidak ada perubahan (1094.0, 6495.0]",
            "variable": "Dieta1_DR1TCALC"
          },
       "ColumnN": {
            "changeStatus": "Status of change compared with existing user lifestyle (True/False)",
            "codeValue": "Possible encoded value for each of the lifestyle variable",
            "comparison": "Changes compared to current value",
            "currentValue": "Current lifestyle interval value",
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

## Contributing

Contributions are welcome (refactoring, adding feature, fixing bugs). No contributions guideline as long as its useful and not violating the main project.
