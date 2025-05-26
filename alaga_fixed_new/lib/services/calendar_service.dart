import 'package:cloud_firestore/cloud_firestore.dart';
import '../models/calendar_event.dart';

class CalendarService {
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;

  Future<List<CalendarEvent>> getEventsForMonth(
      String careProfileId, DateTime month) async {
    // Calculate the start and end dates for the given month
    final firstDay = DateTime(month.year, month.month, 1);
    final lastDay = DateTime(month.year, month.month + 1, 0);

    // Convert to Timestamps for Firestore query
    final firstDayTimestamp = Timestamp.fromDate(firstDay);
    final lastDayTimestamp = Timestamp.fromDate(lastDay);

    final snapshot = await _firestore
        .collection('calendar_events')
        .where('care_profile_id', isEqualTo: careProfileId)
        .where('date', isGreaterThanOrEqualTo: firstDayTimestamp)
        .where('date', isLessThanOrEqualTo: lastDayTimestamp)
        .get();

    return snapshot.docs
        .map((doc) => CalendarEvent.fromFirestore(doc))
        .toList();
  }

  Future<void> updateEventStatus(String eventId, EventStatus status) async {
    await _firestore.collection('calendar_events').doc(eventId).update({
      'status': status.toString().split('.').last,
      'updated_at': Timestamp.now(),
    });
  }

  Future<void> updateMedicationStatusFromEvent(
      String medicationId, EventStatus status) async {
    // Assuming EventStatus can be mapped to MedicationStatus
    // This might need refinement based on actual status values
    String medicationStatus = status.toString().split('.').last;
    await _firestore.collection('medications').doc(medicationId).update({
      'status': medicationStatus,
      'updated_at': Timestamp.now(),
    });
  }

  // Potentially add more methods for adding events, deleting, fetching single event, etc.
}
