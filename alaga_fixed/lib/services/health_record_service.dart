import 'package:cloud_firestore/cloud_firestore.dart';
import '../models/health_record.dart';

class HealthRecordService {
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;

  Future<List<HealthRecord>> getLatestHealthRecordsForCareProfile(
    String careProfileId,
  ) async {
    // This fetches the latest record for each type, similar to the screen logic
    final List<HealthRecord> latestRecords = [];

    for (var type in HealthMetricType.values) {
      final typeStr = type.toString().split('.').last;
      final snapshot = await _firestore
          .collection('health_records')
          .where('care_profile_id', isEqualTo: careProfileId)
          .where('type', isEqualTo: typeStr)
          .orderBy('recorded_at', descending: true)
          .limit(1)
          .get();

      if (snapshot.docs.isNotEmpty) {
        latestRecords.add(HealthRecord.fromFirestore(snapshot.docs.first));
      }
    }

    return latestRecords;
  }

  Future<void> addHealthRecord(HealthRecord record) async {
    await _firestore.collection('health_records').add(record.toFirestore());
  }

  // Potentially add methods for fetching all records of a type, deleting, etc.
}
