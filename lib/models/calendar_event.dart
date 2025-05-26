import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter/material.dart';

enum EventType {
  medication,
  appointment,
  task,
  healthCheck,
  other
}

enum EventStatus {
  pending,
  completed,
  missed,
  skipped,
  taken
}

class CalendarEvent {
  final String id;
  final String title;
  final EventType type;
  final DateTime date;
  final String time;
  final String? description;
  final String careProfileId;
  final String userId;
  final String? relatedId; // ID of related medication, appointment, etc.
  EventStatus status;
  final DateTime createdAt;
  final DateTime updatedAt;

  CalendarEvent({
    required this.id,
    required this.title,
    required this.type,
    required this.date,
    required this.time,
    this.description,
    required this.careProfileId,
    required this.userId,
    this.relatedId,
    this.status = EventStatus.pending,
    required this.createdAt,
    required this.updatedAt,
  });

  factory CalendarEvent.fromFirestore(DocumentSnapshot doc) {
    Map<String, dynamic> data = doc.data() as Map<String, dynamic>;
    return CalendarEvent(
      id: doc.id,
      title: data['title'] ?? '',
      type: _typeFromString(data['type'] ?? 'other'),
      date: (data['date'] as Timestamp).toDate(),
      time: data['time'] ?? '',
      description: data['description'],
      careProfileId: data['care_profile_id'] ?? '',
      userId: data['user_id'] ?? '',
      relatedId: data['related_id'],
      status: _statusFromString(data['status'] ?? 'pending'),
      createdAt: (data['created_at'] as Timestamp).toDate(),
      updatedAt: (data['updated_at'] as Timestamp).toDate(),
    );
  }

  Map<String, dynamic> toFirestore() {
    return {
      'title': title,
      'type': type.toString().split('.').last,
      'date': Timestamp.fromDate(date),
      'time': time,
      'description': description,
      'care_profile_id': careProfileId,
      'user_id': userId,
      'related_id': relatedId,
      'status': status.toString().split('.').last,
      'created_at': Timestamp.fromDate(createdAt),
      'updated_at': Timestamp.fromDate(updatedAt),
    };
  }

  static EventType _typeFromString(String type) {
    switch (type) {
      case 'medication':
        return EventType.medication;
      case 'appointment':
        return EventType.appointment;
      case 'task':
        return EventType.task;
      case 'healthCheck':
        return EventType.healthCheck;
      default:
        return EventType.other;
    }
  }

  static EventStatus _statusFromString(String status) {
    switch (status) {
      case 'completed':
        return EventStatus.completed;
      case 'missed':
        return EventStatus.missed;
      case 'skipped':
        return EventStatus.skipped;
      case 'taken':
        return EventStatus.taken;
      default:
        return EventStatus.pending;
    }
  }

  // Get color based on event type
  Color getEventColor() {
    switch (type) {
      case EventType.medication:
        return Colors.purple.shade300;
      case EventType.appointment:
        return Colors.blue.shade300;
      case EventType.task:
        return Colors.orange.shade300;
      case EventType.healthCheck:
        return Colors.green.shade300;
      case EventType.other:
        return Colors.grey.shade300;
    }
  }

  // Get icon based on event type
  IconData getEventIcon() {
    switch (type) {
      case EventType.medication:
        return Icons.medication;
      case EventType.appointment:
        return Icons.calendar_today;
      case EventType.task:
        return Icons.check_circle;
      case EventType.healthCheck:
        return Icons.favorite;
      case EventType.other:
        return Icons.event_note;
    }
  }

  CalendarEvent copyWith({
    String? id,
    String? title,
    EventType? type,
    DateTime? date,
    String? time,
    String? description,
    String? careProfileId,
    String? userId,
    String? relatedId,
    EventStatus? status,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) {
    return CalendarEvent(
      id: id ?? this.id,
      title: title ?? this.title,
      type: type ?? this.type,
      date: date ?? this.date,
      time: time ?? this.time,
      description: description ?? this.description,
      careProfileId: careProfileId ?? this.careProfileId,
      userId: userId ?? this.userId,
      relatedId: relatedId ?? this.relatedId,
      status: status ?? this.status,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }
}