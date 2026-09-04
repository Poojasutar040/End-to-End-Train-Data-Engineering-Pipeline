import pandas as pd
# LEVEL 1: DATA INGESTION AND INSPECTION

# Task 1.1: Load dataset
df = pd.read_csv("data/raw/train_schedule.csv")

# Task 1.2: Verify records and attributes
print("Total records:", df.shape[0])
print("Total columns:", df.shape[1])

# Task 1.3: Review column names and data types
print("\nColumn names:")
print(df.columns.tolist())

print("\nData types:")
print(df.dtypes)

# Task 1.4: Preserve raw dataset
df_raw = df.copy()

print("\nLevel 1 completed!")

# LEVEL 2: DATA CLEANING AND VALIDATION

# Task 2.1: Identify missing values
print("\nMissing values before cleaning:")
print(df.isnull().sum())


# Task 2.2: Detect duplicate records
print("\nDuplicate records before cleaning:")
print(df.duplicated().sum())

# Remove duplicate records
df = df.drop_duplicates()

print("Duplicate records after cleaning:")
print(df.duplicated().sum())


# Task 2.3: Standardize arrival and departure time

# Convert Arrival_time
df["Arrival_time"] = pd.to_datetime(
    df["Arrival_time"],
    errors="coerce"
)

# Convert Departure_Time
df["Departure_Time"] = pd.to_datetime(
    df["Departure_Time"],
    errors="coerce"
)

# Convert into 24-hour HH:MM format
df["Arrival_time"] = df["Arrival_time"].dt.strftime("%H:%M")
df["Departure_Time"] = df["Departure_Time"].dt.strftime("%H:%M")


# Task 2.4: Save validated dataset
df.to_csv("data/cleaned/validated_train_schedule.csv",
    index=False
)

print("\nLevel 2 completed!")
print("Validated dataset saved successfully.")

# LEVEL 3: DATA PREPARATION AND TRANSFORMATION

# Load validated data from Level 2
df = pd.read_csv(
    "data/cleaned/validated_train_schedule.csv"
)

# Task 3.1: Convert time fields into datetime
df["Arrival_time"] = pd.to_datetime(
    df["Arrival_time"],
    format="%H:%M",
    errors="coerce"
)

df["Departure_Time"] = pd.to_datetime(
    df["Departure_Time"],
    format="%H:%M",
    errors="coerce"
)

# Task 3.3: Organize by train and station sequence
df = df.sort_values(
    by=["Train_No", "Route_Number"]
)
# Task 3.2: Calculate journey duration

df["Next_Arrival_Time"] = df.groupby(
    "Train_No"
)["Arrival_time"].shift(-1)

df["Journey_Duration_Minutes"] = (
    df["Next_Arrival_Time"] - df["Departure_Time"]
).dt.total_seconds() / 60

# Handle journeys crossing midnight
df.loc[
    df["Journey_Duration_Minutes"] < 0,
    "Journey_Duration_Minutes"
] += 24 * 60

# Task 3.4: Prepare dataset for reporting
df = df.drop(
    columns=["Next_Arrival_Time"]
)

print("\nProcessed dataset:")
print(df.head())

print("\nJourney duration:")
print(
    df[
        [
            "Train_No",
            "Station_Name",
            "Journey_Duration_Minutes"
        ]
    ].head(10)
)

# Save processed dataset
df.to_csv(
    "data/processed/train_features.csv",
    index=False
)

print("\nLevel 3 completed!")
print("Processed dataset saved successfully.")

# LEVEL 4: STRUCTURED TABLES AND AGGREGATIONS

# Load processed dataset
df = pd.read_csv("data/processed/train_features.csv")



# Task 4.1: Train-level table - Number of Stops


train_stops = (
    df.groupby("Train_No")
    .size()
    .reset_index(name="Number_of_Stops")
)

print("\nTrain-level table - Number of Stops:")
print(train_stops.head())


# Task 4.2: Train-level table - Total Distance
train_distance = (
    df.groupby("Train_No")["Distance"]
    .max()
    .reset_index(name="Total_Distance")
)

print("\nTrain-level table - Total Distance:")
print(train_distance.head())

# Task 4.3: Train-Station Cross Table


train_station_table = pd.crosstab(
    df["Train_No"],
    df["Station_Name"]
)

print("\nTrain-Station Cross Table:")
print(train_station_table.head())

# Task 4.4: Export Structured Tables


train_stops.to_csv(
    "data/aggregated/train_stops.csv",
    index=False
)

train_distance.to_csv(
    "data/aggregated/train_distance.csv",
    index=False
)

train_station_table.to_csv(
    "data/aggregated/train_station_cross_table.csv"
)

print("\nLevel 4 tables exported successfully.")

# ============================================================
# LEVEL 5: VISUALIZATION AND BASIC PREDICTION
# ============================================================

import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import mean_absolute_error, r2_score


# Load processed data
df = pd.read_csv("data/processed/train_features.csv")


# ============================================================
# Task 5.1: Visualize Train Stops and Total Distance
# ============================================================

# Number of stops
train_stops = (
    df.groupby("Train_No")
    .size()
    .reset_index(name="Number_of_Stops")
)

plt.figure(figsize=(12, 6))
plt.bar(
    train_stops["Train_No"].astype(str),
    train_stops["Number_of_Stops"]
)
plt.xlabel("Train Number")
plt.ylabel("Number of Stops")
plt.title("Number of Stops per Train")
plt.xticks(rotation=90)
plt.tight_layout()
plt.show()


# Total distance
train_distance = (
    df.groupby("Train_No")["Distance"]
    .max()
    .reset_index(name="Total_Distance")
)

plt.figure(figsize=(12, 6))
plt.bar(
    train_distance["Train_No"].astype(str),
    train_distance["Total_Distance"]
)
plt.xlabel("Train Number")
plt.ylabel("Total Distance")
plt.title("Total Distance per Train")
plt.xticks(rotation=90)
plt.tight_layout()
plt.show()


# ============================================================
# Task 5.2: Journey Duration Distribution
# ============================================================

plt.figure(figsize=(10, 6))

plt.hist(
    df["Journey_Duration_Minutes"].dropna(),
    bins=30
)

plt.xlabel("Journey Duration (Minutes)")
plt.ylabel("Number of Records")
plt.title("Distribution of Journey Duration")

plt.tight_layout()
plt.show()


# ============================================================
# Task 5.3: Train-Test Split
# ============================================================

features = [
    "Train_No",
    "Route_Number",
    "Distance"
]

target = "Journey_Duration_Minutes"

model_data = df[features + [target]].dropna()

X = model_data[features]
y = model_data[target]

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42
)

print("\nTraining records:", len(X_train))
print("Testing records:", len(X_test))


# ============================================================
# Task 5.4: Decision Tree Prediction
# ============================================================

model = DecisionTreeRegressor(
    random_state=42
)

model.fit(X_train, y_train)

y_pred = model.predict(X_test)

mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print("\nModel Results:")
print("Mean Absolute Error:", mae)
print("R2 Score:", r2)

# ============================================================
# LEVEL 6: FINAL INDUSTRY-STYLE DATA ENGINEERING PROJECT
# ============================================================

from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import mean_absolute_error, r2_score
import joblib


# ------------------------------------------------------------
# Task 6.1: Build Decision Tree Model
# ------------------------------------------------------------

# Load prepared dataset
df = pd.read_csv("data/processed/train_features.csv")

print("\nPrepared dataset loaded successfully.")
print("Total records:", len(df))


# Select features
features = [
    "Train_No",
    "Route_Number",
    "Distance"
]

# Target variable
target = "Journey_Duration_Minutes"


# Create ML dataset
model_data = df[features + [target]].dropna()

print("Records available for ML:", len(model_data))


# Separate input and output
X = model_data[features]
y = model_data[target]


# Split dataset
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42
)


print("\nTraining records:", len(X_train))
print("Testing records:", len(X_test))


# Create Decision Tree model
model = DecisionTreeRegressor(
    max_depth=10,
    random_state=42
)


# Train model
model.fit(X_train, y_train)

print("\nDecision Tree model trained successfully.")


# Make predictions
y_pred = model.predict(X_test)


# Evaluate model
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)


print("\n========== MODEL PERFORMANCE ==========")
print("Mean Absolute Error:", round(mae, 2))
print("R2 Score:", round(r2, 2))


# Save trained model
joblib.dump(
    model,
    "models/train_journey_duration_model.pkl"
)

print("\nModel saved successfully.")
print("Location: models/train_journey_duration_model.pkl")