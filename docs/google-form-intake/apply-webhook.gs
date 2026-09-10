/**
 * HireLens AI — Google Form intake bridge.
 *
 * Setup: see README.md in this folder. Short version — paste this into
 * the Form's Script editor (⋮ menu → Script editor), fill in the two
 * constants below, then add an installable trigger:
 *   Triggers (clock icon) → Add Trigger → onFormSubmit → From form →
 *   On form submit
 */

// ---- Configure these two before using ----
const BACKEND_URL = 'https://your-backend-url.example.com'; // no trailing slash; can't be localhost, see README §4
const API_KEY = 'PASTE_PUBLIC_APPLY_API_KEY_HERE'; // from backend/.env's PUBLIC_APPLY_API_KEY
// -------------------------------------------

// Must match the Form's question titles exactly (README §1).
const QUESTION = {
  NAME: 'Nama Lengkap',
  EMAIL: 'Email',
  PHONE: 'No. Telepon',
  JOB: 'Posisi yang Dilamar',
  CV: 'CV (PDF/DOCX)',
};

function onFormSubmit(e) {
  try {
    const answers = {};
    e.response.getItemResponses().forEach((itemResponse) => {
      answers[itemResponse.getItem().getTitle()] = itemResponse.getResponse();
    });

    // A file-upload question's response is an array of Drive file ids
    // (one per uploaded file) — not a normal string answer.
    const fileIds = answers[QUESTION.CV];
    if (!fileIds || fileIds.length === 0) {
      throw new Error('Tidak ada file CV pada submission ini');
    }
    const cvBlob = DriveApp.getFileById(fileIds[0]).getBlob();

    // UrlFetchApp auto-encodes as multipart/form-data when any payload
    // value is a Blob — no manual boundary handling needed.
    const payload = {
      job_title: answers[QUESTION.JOB],
      full_name: answers[QUESTION.NAME],
      email: answers[QUESTION.EMAIL],
      phone: answers[QUESTION.PHONE],
      cv_file: cvBlob,
    };

    const response = UrlFetchApp.fetch(BACKEND_URL + '/api/v1/public/apply', {
      method: 'post',
      headers: { 'X-API-Key': API_KEY },
      payload: payload,
      muteHttpExceptions: true, // so a 4xx/5xx doesn't throw — handle it below instead
    });

    const status = response.getResponseCode();
    Logger.log('HireLens response %s: %s', status, response.getContentText());

    if (status >= 400) {
      notifyFailure_(answers, `Status ${status}: ${response.getContentText()}`);
    }
  } catch (err) {
    Logger.log('onFormSubmit error: %s', err);
    notifyFailure_({}, String(err));
  }
}

/** Best-effort — a silent drop is worse than a noisy failure for a test channel. */
function notifyFailure_(answers, detail) {
  try {
    const who = Session.getActiveUser().getEmail();
    if (!who) return; // no email identity available in this context
    MailApp.sendEmail(
      who,
      'HireLens intake gagal',
      `${detail}\n\nPelamar: ${answers[QUESTION.NAME] || '?'} (${answers[QUESTION.EMAIL] || '?'})`
    );
  } catch (mailErr) {
    Logger.log('notifyFailure_ itself failed: %s', mailErr);
  }
}
