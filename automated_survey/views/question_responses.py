from twilio.twiml.messaging_response import MessagingResponse
from twilio.twiml.voice_response import VoiceResponse

from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.views.decorators.http import require_POST

from automated_survey.models import QuestionResponse, Question


#@require_POST
def save_response(request, survey_id, question_id):
    print('save_responses')
    question = Question.objects.get(id=question_id)

    save_response_from_request(request, question)

    next_question = question.next()
    if not next_question:
        return goodbye(request)
    else:
        return next_question_redirect(next_question.id, survey_id)


def next_question_redirect(question_id, survey_id):
    print('next_question_redirect')
    parameters = {'survey_id': survey_id, 'question_id': question_id}
    question_url = reverse('question', kwargs=parameters)

    twiml_response = MessagingResponse()
    twiml_response.redirect(url=question_url, method='GET')
    return HttpResponse(twiml_response)


def goodbye(request):
    goodbye_messages = ['That was the last question',
                        'Thank you for taking this survey',
                        'Good-bye']
    if request.is_sms:
        response = MessagingResponse()
        [response.message(message) for message in goodbye_messages]
    else:
        response = VoiceResponse()
        [response.say(message) for message in goodbye_messages]
        response.hangup()

    return HttpResponse(response)


def save_response_from_request(request, question):
    print('save_response_from_request')
    session_id = request.POST['MessageSid' if request.is_sms else 'CallSid']
    print('session_id')
    print(session_id)
    request_body = _extract_request_body(request, question.kind)
    print('request_body')
    print(request_body)
    phone_number = request.POST['From']
    print(phone_number)

    response = QuestionResponse.objects.filter(question_id=question.id,
                                               call_sid=session_id).first()
    print(response)

    if not response:
        print("not respnse")
        QuestionResponse(call_sid=session_id,
                         phone_number=phone_number,
                         response=request_body,
                         question=question).save()
    else:
        print("response save")
        response.response = request_body
        response.save()


def _extract_request_body(request, question_kind):
    Question.validate_kind(question_kind)

    if request.is_sms:
        key = 'Body'
    elif question_kind in [Question.YES_NO, Question.NUMERIC]:
        key = 'Digits'
    elif 'TranscriptionText' in request.POST:
        key = 'TranscriptionText'
    else:
        key = 'RecordingUrl'

    return request.POST.get(key)
