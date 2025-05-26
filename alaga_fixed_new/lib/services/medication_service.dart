import 'package:cloud_firestore/cloud_firestore.dart';
import '../models/medication.dart';

class MedicationService {
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;

  Stream<List<Medication>> getMedicationsForCareProfile(String careProfileId) {
    return _firestore
        .collection('medications')
        .where('care_profile_id', isEqualTo: careProfileId)
        .orderBy('time')
        .snapshots()
        .map((snapshot) =>
            snapshot.docs.map((doc) => Medication.fromFirestore(doc)).toList());
  }

  Future<void> addMedication(Medication medication) async {
    await _firestore.collection('medications').add(medication.toFirestore());
  }

  Future<void> updateMedicationStatus(
      String medicationId, MedicationStatus status) async {
    await _firestore.collection('medications').doc(medicationId).update({
      'status': status.toString().split('.').last,
      'updated_at': Timestamp.now(),
    });
  }

  // Potentially add more methods for deleting, fetching single medication, etc.
}
