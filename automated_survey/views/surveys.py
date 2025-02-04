from automated_survey.models import Survey, Question
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.views.decorators.http import require_POST, require_GET, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from twilio.twiml.voice_response import VoiceResponse
from twilio.twiml.messaging_response import MessagingResponse

# Have separate code running
# phone_number, survey_id
# def send_texts():
#  for each row in phone_number, survey_id:
#      


@require_GET
def show_survey_results(request, survey_id):
    survey = Survey.objects.get(id=survey_id)
    responses_to_render = [response.as_dict() for response in survey.responses]

    template_context = {
        'responses': responses_to_render,
        'survey_title': survey.title
    }

    return render_to_response('results.html', context=template_context)


@csrf_exempt
def show_survey(request, survey_id):
    survey = Survey.objects.get(id=survey_id)
    first_question = survey.first_question

    first_question_ids = {
        'survey_id': survey.id,
        'question_id': first_question.id
    }

    first_question_url = reverse('question', kwargs=first_question_ids)

    welcome = 'Hello and thank you for taking the %s survey' % survey.title
    if request.is_sms:
        twiml_response = MessagingResponse()
        twiml_response.message(welcome)
        twiml_response.redirect(first_question_url, method='GET')
    else:
        twiml_response = VoiceResponse()
        twiml_response.say(welcome)
        twiml_response.redirect(first_question_url, method='GET')

    return HttpResponse(twiml_response, content_type='application/xml')


@require_http_methods(["GET", "POST"])
def redirects_twilio_request_to_proper_endpoint(request):
    print("HELLOOOO!")
    print(request.session)
    print("EXISTS")
    #print(request.session.exists())
    #print(request.Session.objects.all())
    print("GREAT")
    #print(request.session['answering_question_id'])
    print(request.session.get('answering_question_id', 'false'))
    print("OKAY")
    answering_question = request.session.get('answering_question_id')
    print("YEPPERS")
    if not answering_question:
        print('1')
        first_survey = Survey.objects.first()
        redirect_url = reverse('survey',
                               kwargs={'survey_id': first_survey.id})
    else:
        print('2')
        question = Question.objects.get(id=answering_question)
        redirect_url = reverse('save_response',
                               kwargs={'survey_id': question.survey.id,
                                       'question_id': question.id})
        print(redirect_url)
    return HttpResponseRedirect(redirect_url)


@require_GET
def redirect_to_first_results(request):
    first_survey = Survey.objects.first()
    results_for_first_survey = reverse(
        'survey_results', kwargs={
            'survey_id': first_survey.id})
    return HttpResponseRedirect(results_for_first_survey)
