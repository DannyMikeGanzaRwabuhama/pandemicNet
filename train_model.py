import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score
import pickle

# Load data
data = np.load('contact_data.npz')
X = data['X']
y = data['y']

# Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train Random Forest
model = RandomForestClassifier(
    n_estimators=300,
    max_depth=10,
    min_samples_leaf=10,
    max_features='sqrt',
    random_state=42
)
model.fit(X_train, y_train)

# Test set accuracy
y_pred = model.predict(X_test)
test_accuracy = accuracy_score(y_test, y_pred)
print(f"Test set accuracy: {test_accuracy:.2f}")

# Cross-validation
cv_scores = cross_val_score(model, X, y, cv=5)
print(f"Cross-validation scores: {cv_scores}")
print(f"Average CV accuracy: {cv_scores.mean():.2f} (+/- {cv_scores.std() * 2:.2f})")

# Feature importance
print("Feature importance:",
      dict(zip(['direct_contacts', 'days_since_last', 'mutual_contacts'], model.feature_importances_)))

# Save
with open('contact_model.pkl', 'wb') as f:  # type: BinaryIO
    pickle.dump(model, f)

print("Model trained and saved as contact_model.pkl")
