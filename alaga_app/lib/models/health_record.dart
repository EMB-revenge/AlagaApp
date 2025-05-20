import 'package:cloud_firestore/cloud_firestore.dart';

enum HealthMetricType {
  heartRate,
  bloodPressure,
  glucoseLevel,
  temperature,
  weight,
  oxygenLevel,
  other
}

class HealthRecord {
  final String id;
  final HealthMetricType type;
  final String value;
  final String unit;
  final String? notes;
  final String careProfileId;
  final String userId;
  final DateTime recordedAt;
  final DateTime createdAt;

  HealthRecord({
    required this.id,
    required this.type,
    required this.value,
    required this.unit,
    this.notes,
    required this.careProfileId,
    required this.userId,
    required this.recordedAt,
    required this.createdAt,
  });

  factory HealthRecord.fromFirestore(DocumentSnapshot doc) {
    Map<String, dynamic> data = doc.data() as Map<String, dynamic>;
    return HealthRecord(
      id: doc.id,
      type: _typeFromString(data['type'] ?? 'other'),
      value: data['value'] ?? '',
      unit: data['unit'] ?? '',
      notes: data['notes'],
      careProfileId: data['care_profile_id'] ?? '',
      userId: data['user_id'] ?? '',
      recordedAt: (data['recorded_at'] as Timestamp).toDate(),
      createdAt: (data['created_at'] as Timestamp).toDate(),
    );
  }

  Map<String, dynamic> toFirestore() {
    return {
      'type': type.toString().split('.').last,
      'value': value,
      'unit': unit,
      'notes': notes,
      'care_profile_id': careProfileId,
      'user_id': userId,
      'recorded_at': Timestamp.fromDate(recordedAt),
      'created_at': Timestamp.fromDate(createdAt),
    };
  }

  static HealthMetricType _typeFromString(String type) {
    switch (type) {
      case 'heartRate':
        return HealthMetricType.heartRate;
      case 'bloodPressure':
        return HealthMetricType.bloodPressure;
      case 'glucoseLevel':
        return HealthMetricType.glucoseLevel;
      case 'temperature':
        return HealthMetricType.temperature;
      case 'weight':
        return HealthMetricType.weight;
      case 'oxygenLevel':
        return HealthMetricType.oxygenLevel;
      default:
        return HealthMetricType.other;
    }
  }

  // Helper method to get the display name for the health metric type
  static String getDisplayName(HealthMetricType type) {
    switch (type) {
      case HealthMetricType.heartRate:
        return 'Heart Rate';
      case HealthMetricType.bloodPressure:
        return 'Blood Pressure';
      case HealthMetricType.glucoseLevel:
        return 'Glucose Level';
      case HealthMetricType.temperature:
        return 'Temperature';
      case HealthMetricType.weight:
        return 'Weight';
      case HealthMetricType.oxygenLevel:
        return 'Oxygen Level';
      case HealthMetricType.other:
        return 'Other';
    }
  }

  // Helper method to get the default unit for a health metric type
  static String getDefaultUnit(HealthMetricType type) {
    switch (type) {
      case HealthMetricType.heartRate:
        return 'bpm';
      case HealthMetricType.bloodPressure:
        return 'mm Hg';
      case HealthMetricType.glucoseLevel:
        return 'mg/dL';
      case HealthMetricType.temperature:
        return '°C';
      case HealthMetricType.weight:
        return 'kg';
      case HealthMetricType.oxygenLevel:
        return '%';
      case HealthMetricType.other:
        return '';
    }
  }
}