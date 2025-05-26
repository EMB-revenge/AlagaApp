import 'package:cloud_firestore/cloud_firestore.dart';

enum MedicationStatus {
  pending,
  taken,
  skipped,
  missed
}

class Medication {
  final String id;
  final String name;
  final String dosage;
  final String frequency;
  final String time;
  final String careProfileId;
  final String userId;
  MedicationStatus status;
  final DateTime createdAt;
  final DateTime updatedAt;

  Medication({
    required this.id,
    required this.name,
    required this.dosage,
    required this.frequency,
    required this.time,
    required this.careProfileId,
    required this.userId,
    this.status = MedicationStatus.pending,
    required this.createdAt,
    required this.updatedAt,
  });

  factory Medication.fromFirestore(DocumentSnapshot doc) {
    Map<String, dynamic> data = doc.data() as Map<String, dynamic>;
    return Medication(
      id: doc.id,
      name: data['name'] ?? '',
      dosage: data['dosage'] ?? '',
      frequency: data['frequency'] ?? '',
      time: data['time'] ?? '',
      careProfileId: data['care_profile_id'] ?? '',
      userId: data['user_id'] ?? '',
      status: _statusFromString(data['status'] ?? 'pending'),
      createdAt: (data['created_at'] as Timestamp).toDate(),
      updatedAt: (data['updated_at'] as Timestamp).toDate(),
    );
  }

  Map<String, dynamic> toFirestore() {
    return {
      'name': name,
      'dosage': dosage,
      'frequency': frequency,
      'time': time,
      'care_profile_id': careProfileId,
      'user_id': userId,
      'status': status.toString().split('.').last,
      'created_at': Timestamp.fromDate(createdAt),
      'updated_at': Timestamp.fromDate(updatedAt),
    };
  }

  static MedicationStatus _statusFromString(String status) {
    switch (status) {
      case 'taken':
        return MedicationStatus.taken;
      case 'skipped':
        return MedicationStatus.skipped;
      case 'missed':
        return MedicationStatus.missed;
      default:
        return MedicationStatus.pending;
    }
  }

  Medication copyWith({
    String? id,
    String? name,
    String? dosage,
    String? frequency,
    String? time,
    String? careProfileId,
    String? userId,
    MedicationStatus? status,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) {
    return Medication(
      id: id ?? this.id,
      name: name ?? this.name,
      dosage: dosage ?? this.dosage,
      frequency: frequency ?? this.frequency,
      time: time ?? this.time,
      careProfileId: careProfileId ?? this.careProfileId,
      userId: userId ?? this.userId,
      status: status ?? this.status,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }
}