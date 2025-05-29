import 'package:cloud_firestore/cloud_firestore.dart';
import '../models/medication.dart';

// Handles all medication-related database operations
class MedicationService {
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;

  // Get real-time list of medications for a specific person
  Stream<List<Medication>> getMedicationsForCareProfile(String careProfileId) {
    return _firestore
        .collection('medications')
        .where('care_profile_id', isEqualTo: careProfileId)
        .orderBy('time')
        .snapshots()
        .map((snapshot) =>
            snapshot.docs.map((doc) => Medication.fromFirestore(doc)).toList());
  }

  // Add a new medication to the database
  Future<void> addMedication(Medication medication) async {
    await _firestore.collection('medications').add(medication.toFirestore());
  }

  // Update whether a medication was taken, skipped, or missed
  Future<void> updateMedicationStatus(
      String medicationId, MedicationStatus status) async {
    await _firestore.collection('medications').doc(medicationId).update({
      'status': status.toString().split('.').last,
      'updated_at': Timestamp.now(),
    });
  }

  // Potentially add more methods for deleting, fetching single medication, etc.
}
