import 'package:cloud_firestore/cloud_firestore.dart';

class CareProfile {
  final String id;
  final String name;
  final String? photoUrl;
  final String? relationship;
  final int? age;
  final String? gender;
  final String userId;
  final DateTime createdAt;
  final DateTime updatedAt;

  CareProfile({
    required this.id,
    required this.name,
    this.photoUrl,
    this.relationship,
    this.age,
    this.gender,
    required this.userId,
    required this.createdAt,
    required this.updatedAt,
  });

  factory CareProfile.fromFirestore(DocumentSnapshot doc) {
    Map<String, dynamic> data = doc.data() as Map<String, dynamic>;
    return CareProfile(
      id: doc.id,
      name: data['name'] ?? '',
      photoUrl: data['photo_url'],
      relationship: data['relationship'],
      age: data['age'],
      gender: data['gender'],
      userId: data['user_id'] ?? '',
      createdAt: (data['created_at'] as Timestamp).toDate(),
      updatedAt: (data['updated_at'] as Timestamp).toDate(),
    );
  }

  Map<String, dynamic> toFirestore() {
    return {
      'name': name,
      'photo_url': photoUrl,
      'relationship': relationship,
      'age': age,
      'gender': gender,
      'user_id': userId,
      'created_at': Timestamp.fromDate(createdAt),
      'updated_at': Timestamp.fromDate(updatedAt),
    };
  }

  CareProfile copyWith({
    String? id,
    String? name,
    String? photoUrl,
    String? relationship,
    int? age,
    String? gender,
    String? userId,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) {
    return CareProfile(
      id: id ?? this.id,
      name: name ?? this.name,
      photoUrl: photoUrl ?? this.photoUrl,
      relationship: relationship ?? this.relationship,
      age: age ?? this.age,
      gender: gender ?? this.gender,
      userId: userId ?? this.userId,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }
}