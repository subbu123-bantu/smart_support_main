from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from asgiref.sync import async_to_sync
from django.test import TestCase
from requests import HTTPError, RequestException

from tickets.ai.ai import (
    best_keyword_category,
    choose_final,
    log_prediction,
    needs_manual_review,
    predict_ticket,
    resolve_low_confidence,
    rule_engine,
)
from tickets.ai import ai_client
from tickets.ai.ai_client import (
    GroqTicketClassifier,
    ai_classification,
    ai_classification_async,
    build_groq_payload,
    build_groq_prompt,
    call_groq,
    call_groq_async,
    parse_ai_result,
)
from tickets.ai.ai_dataset import format_examples_for_prompt
from tickets.ai.ai_helper import count_generic_only, is_generic_input, is_weak_input, phrase_score, preprocess
from tickets.ai.ai_overrides import apply_conflict_overrides, apply_override, starts_with_refund_request
from tickets.ai.ai_priority import (
    acc_category,
    auth_category,
    bill_category,
    get_priority,
    network_category,
    tech_category,
)
from tickets.exceptions import EmailSendError
from tickets.models import Category, Ticket, TicketPredictionLog
from tickets.tasks import send_email_task
from users.models import User

from .test_utils import PASSWORD_FIELD, build_test_password


class TicketAiHelpersTests(TestCase):
    def test_preprocess_normalizes_whitespace_and_punctuation(self):
        self.assertEqual(preprocess("  Server ERROR!!! \n "), "server error")

    def test_phrase_score_counts_single_and_multi_word_matches(self):
        score, matches = phrase_score("payment failed and refund pending", ["payment", "payment failed", "refund"])
        self.assertEqual(score, 5)
        self.assertEqual(matches, ["payment", "payment failed", "refund"])

    def test_generic_and_weak_input_helpers_cover_edge_cases(self):
        self.assertTrue(count_generic_only([]))
        self.assertTrue(is_weak_input(["help"], "help"))
        self.assertTrue(is_generic_input(["issue", "problem"], "issue problem"))
        self.assertFalse(is_generic_input(["invoice", "refund"], "invoice refund"))


class TicketAiOverrideAndPriorityTests(TestCase):
    def test_category_specific_priority_helpers_cover_additional_branches(self):
        self.assertEqual(bill_category("refund not received after cancellation"), "medium")
        self.assertEqual(bill_category("payment page shows server error after money deduction"), "high")
        self.assertEqual(bill_category("gst details how to update invoice information"), "low")
        self.assertEqual(bill_category("invoice not visible on invoice page"), "high")

        self.assertEqual(tech_category("server error 500 crash exception"), "high")
        self.assertEqual(tech_category("feature not working and very slow"), "medium")
        self.assertEqual(tech_category("critical dashboard crash for all users"), "urgent")

        self.assertEqual(network_category("fails on office wifi network"), "high")
        self.assertEqual(network_category("slow internet latency disconnect issue"), "high")
        self.assertEqual(network_category("network completely down for all users"), "urgent")
        self.assertEqual(network_category("internet connection keeps disconnecting"), "high")

        self.assertEqual(auth_category("cannot login due to invalid credentials and 2fa issue"), "high")
        self.assertEqual(auth_category("session expired after password reset verification link"), "medium")
        self.assertEqual(auth_category("otp is not coming to my mobile number"), "high")

        self.assertEqual(acc_category("delete my account permanently"), "medium")
        self.assertEqual(acc_category("change email address change requested"), "low")
        self.assertEqual(acc_category("my account details are incorrect"), "medium")
        self.assertEqual(acc_category("update profile display name"), "low")

    def test_apply_override_updates_category_source_and_confidence(self):
        final = {"category": "other", "source": "fallback", "confidence": 0.2}
        apply_override(final, "billing", "billing_override", 0.88)
        self.assertEqual(final, {"category": "billing", "source": "billing_override", "confidence": 0.88})

    def test_starts_with_refund_request_detects_refund_prefixes(self):
        self.assertTrue(starts_with_refund_request(" refund was charged twice"))
        self.assertTrue(starts_with_refund_request("need refund immediately"))
        self.assertFalse(starts_with_refund_request("please help with refund"))

    def test_apply_conflict_overrides_shifts_to_billing_for_refund_wording(self):
        final = {"category": "technical", "source": "rule", "confidence": 0.72}
        updated = apply_conflict_overrides("refund request because app crash charged twice", final)
        self.assertEqual(updated["category"], "billing")
        self.assertEqual(updated["source"], "billing_override")

    def test_apply_conflict_overrides_prefers_billing_for_payment_error_with_money_deducted(self):
        final = {"category": "technical", "source": "rule", "confidence": 0.90}
        updated = apply_conflict_overrides("payment page shows server error after money deducted", final)
        self.assertEqual(updated["category"], "billing")
        self.assertEqual(updated["source"], "billing_override")

    def test_apply_conflict_overrides_shifts_to_authentication_when_verification_link_present(self):
        final = {"category": "account", "source": "rule", "confidence": 0.70}
        updated = apply_conflict_overrides("verification link is invalid and login fails", final)
        self.assertEqual(updated["category"], "authentication")
        self.assertEqual(updated["source"], "auth_override")

    def test_get_priority_covers_urgent_category_specific_and_default_paths(self):
        self.assertEqual(get_priority("production down for all users", "technical"), "urgent")
        self.assertEqual(get_priority("payment failed and charged twice", "billing"), "high")
        self.assertEqual(get_priority("cannot connect to dashboard after login", "network"), "medium")
        self.assertEqual(get_priority("password reset verification link expired", "authentication"), "medium")
        self.assertEqual(get_priority("update profile display name", "account"), "low")
        self.assertEqual(get_priority("cannot access because error failed", None), "medium")
        self.assertEqual(get_priority("error happened but user can still continue", None), "low")


class TicketAiClientTests(TestCase):
    def setUp(self):
        ai_client._groq_cooldown_until = 0.0

    def test_build_groq_payload_uses_expected_model_and_prompt_shape(self):
        payload = build_groq_payload("Classify this ticket")
        self.assertIn("model", payload)
        self.assertEqual(payload["messages"][1]["content"], "Classify this ticket")
        self.assertEqual(payload["temperature"], 0.1)

    def test_build_groq_prompt_includes_reference_examples(self):
        examples = format_examples_for_prompt()
        prompt = build_groq_prompt("router timeout")
        self.assertIn("Reference examples:", prompt)
        self.assertIn(examples, prompt)
        self.assertIn("router timeout", prompt)

    def test_classifier_instance_builds_payload_with_custom_model(self):
        classifier = GroqTicketClassifier(api_key="token", model="demo-model")
        payload = classifier.build_payload("Prompt text")
        self.assertEqual(payload["model"], "demo-model")
        self.assertEqual(payload["messages"][1]["content"], "Prompt text")

    @patch("tickets.ai.ai_client.GROQ_API_KEY", None)
    def test_call_groq_returns_none_without_api_key(self):
        self.assertIsNone(call_groq("ticket text"))

    @patch("tickets.ai.ai_client.requests.post")
    @patch("tickets.ai.ai_client.GROQ_API_KEY", "token")
    def test_call_groq_returns_message_content_on_success(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {"choices": [{"message": {"content": '{"category":"billing","confidence":0.81}'}}]}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        self.assertEqual(call_groq("ticket text"), '{"category":"billing","confidence":0.81}')

    @patch("tickets.ai.ai_client.requests.post", side_effect=RequestException("network down"))
    @patch("tickets.ai.ai_client.GROQ_API_KEY", "token")
    def test_call_groq_returns_none_on_request_failure(self, _mock_post):
        self.assertIsNone(call_groq("ticket text"))

    @patch("tickets.ai.ai_client.requests.post")
    @patch("tickets.ai.ai_client.time.monotonic", return_value=100.0)
    @patch("tickets.ai.ai_client.GROQ_API_KEY", "token")
    def test_call_groq_starts_cooldown_after_rate_limit(self, mock_monotonic, mock_post):
        response = Mock(status_code=429, headers={"Retry-After": "7"})
        error = HTTPError("rate limited")
        error.response = response

        mock_response = Mock()
        mock_response.raise_for_status.side_effect = error
        mock_post.return_value = mock_response

        self.assertIsNone(call_groq("ticket text"))
        self.assertEqual(ai_client._groq_cooldown_until, 107.0)
        mock_monotonic.assert_called()

    @patch("tickets.ai.ai_client.requests.post")
    @patch("tickets.ai.ai_client.time.monotonic", return_value=50.0)
    @patch("tickets.ai.ai_client.GROQ_API_KEY", "token")
    def test_call_groq_skips_request_during_cooldown(self, mock_monotonic, mock_post):
        ai_client._groq_cooldown_until = 55.0

        self.assertIsNone(call_groq("ticket text"))
        mock_post.assert_not_called()
        mock_monotonic.assert_called_once()

    def test_parse_ai_result_accepts_json_and_clamps_confidence(self):
        parsed = parse_ai_result('{"category":"technical","confidence":0.99}')
        self.assertEqual(parsed["category"], "technical")
        self.assertEqual(parsed["confidence"], 0.88)
        self.assertEqual(parsed["source"], "AI")

    def test_parse_ai_result_returns_none_for_invalid_payload(self):
        self.assertIsNone(parse_ai_result("not-json"))

    @patch("tickets.ai.ai_client.call_groq")
    def test_ai_classification_uses_call_and_parse_pipeline(self, mock_call_groq):
        mock_call_groq.return_value = '{"category":"network","confidence":0.67}'
        result = ai_classification("router timeout")
        self.assertEqual(result["category"], "network")
        self.assertEqual(result["source"], "AI")

    @patch("tickets.ai.ai_client.call_groq_async", new_callable=AsyncMock)
    def test_ai_classification_async_uses_call_and_parse_pipeline(self, mock_call_groq_async):
        mock_call_groq_async.return_value = '{"category":"network","confidence":0.67}'
        result = async_to_sync(ai_classification_async)("router timeout")
        self.assertEqual(result["category"], "network")
        self.assertEqual(result["source"], "AI")


class TicketAiDecisionTests(TestCase):
    def test_rule_engine_returns_short_input_fallback(self):
        result = rule_engine("help")
        self.assertEqual(result["category"], "other")
        self.assertEqual(result["source"], "rule_short_input")

    def test_rule_engine_scores_billing_keywords(self):
        result = rule_engine("payment failed and refund deducted twice")
        self.assertEqual(result["category"], "billing")
        self.assertEqual(result["source"], "rule")
        self.assertGreater(result["confidence"], 0.78)

    def test_best_keyword_category_returns_none_without_matches(self):
        self.assertIsNone(best_keyword_category("completely unrelated wording"))

    def test_choose_final_prefers_agreeing_rule_and_ai(self):
        result = choose_final(
            {"category": "billing", "confidence": 0.8, "source": "rule"},
            {"category": "billing", "confidence": 0.82, "source": "AI"},
            None,
        )
        self.assertEqual(result, {"category": "billing", "confidence": 0.86, "source": "rule+AI"})

    def test_choose_final_prefers_highest_confidence_when_sources_disagree(self):
        result = choose_final(
            {"category": "billing", "confidence": 0.8, "source": "rule"},
            {"category": "technical", "confidence": 0.84, "source": "AI"},
            {"category": "network", "confidence": 0.7, "source": "keyword_fallback"},
        )
        self.assertEqual(result["category"], "technical")

    def test_resolve_low_confidence_uses_soft_fallback_and_threshold_reject(self):
        final = {"source": "rule"}
        category, confidence = resolve_low_confidence(
            "billing",
            0.6,
            final,
            {"category": "technical", "confidence": 0.71, "matches": ["server error", "dashboard"]},
        )
        self.assertEqual((category, confidence, final["source"]), ("technical", 0.72, "soft_fallback"))

        final = {"source": "rule"}
        category, confidence = resolve_low_confidence(
            "billing",
            0.6,
            final,
            {"category": "technical", "confidence": 0.71, "matches": ["server error"]},
        )
        self.assertEqual((category, confidence, final["source"]), ("other", 0.48, "threshold_reject"))

    def test_needs_manual_review_flags_low_confidence_and_fallback_sources(self):
        self.assertTrue(needs_manual_review("other", 0.9, "rule"))
        self.assertTrue(needs_manual_review("billing", 0.8, "rule"))
        self.assertTrue(needs_manual_review("billing", 0.9, "soft_fallback"))
        self.assertFalse(needs_manual_review("billing", 0.9, "rule"))

    @patch("tickets.ai.ai.ai_classification")
    def test_predict_ticket_rejects_weak_and_generic_inputs_before_ai(self, mock_ai_classification):
        weak = predict_ticket("help")
        generic = predict_ticket("help issue problem update")
        self.assertEqual(weak["source"], "weak_input_reject")
        self.assertEqual(generic["source"], "generic_input_reject")
        mock_ai_classification.assert_not_called()

    @patch("tickets.ai.ai.apply_conflict_overrides")
    @patch("tickets.ai.ai.ai_classification")
    def test_predict_ticket_handles_invalid_final_category_and_returns_priority(self, mock_ai_classification, mock_apply_conflict_overrides):
        mock_ai_classification.return_value = {"category": "technical", "confidence": 0.84, "source": "AI"}
        mock_apply_conflict_overrides.return_value = {"category": "unknown", "confidence": 0.9, "source": "weird"}
        result = predict_ticket("dashboard crashes with server error")
        self.assertEqual(result["category"], "other")
        self.assertEqual(result["source"], "fallback")
        self.assertEqual(result["priority"], "low")
        self.assertTrue(result["needs_manual_review"])

    @patch("tickets.ai.ai.ai_classification")
    def test_predict_ticket_returns_resolved_category_for_real_input(self, mock_ai_classification):
        mock_ai_classification.return_value = {"category": "billing", "confidence": 0.86, "source": "AI"}
        result = predict_ticket("payment failed and invoice page not loading")
        self.assertEqual(result["category"], "billing")
        self.assertIn(result["source"], {"rule+AI", "billing_override", "soft_fallback", "rule"})
        self.assertIn(result["priority"], {"high", "medium", "urgent", "low"})

    def test_log_prediction_creates_prediction_log_record(self):
        ticket = Ticket.objects.create(
            title="Logged prediction",
            description="Track this prediction",
            category=Category.objects.create(name="logged"),
            priority=Ticket.Priority.LOW,
            customer=User.objects.create_user(
                username="logger-customer",
                email="logger-customer@example.com",
                **{PASSWORD_FIELD: build_test_password()},
                role="customer",
            ),
            user_ticket_id=1,
        )
        log_prediction("ticket text", {"category": "billing", "priority": "high", "source": "rule", "confidence": 0.77}, ticket)
        log = TicketPredictionLog.objects.get(ticket=ticket)
        self.assertEqual(log.predicted_category, "billing")
        self.assertEqual(log.predicted_priority, "high")


class TicketTaskAndExceptionTests(TestCase):
    def test_email_send_error_formats_status_and_message(self):
        error = EmailSendError(status_code=400, message="Bad request")
        self.assertEqual(str(error), "[400] Bad request")
        self.assertEqual(error.status_code, 400)

    @patch("tickets.tasks.logger")
    @patch("tickets.tasks.requests.post")
    @patch("tickets.tasks.render_to_string", return_value="<p>Hello</p>")
    def test_send_email_task_logs_success_for_200_responses(self, _mock_render, mock_post, mock_logger):
        mock_post.return_value = SimpleNamespace(status_code=201, text="created")
        send_email_task.run("user@example.com", "Subject", context={"name": "User"})
        mock_post.assert_called_once()
        mock_logger.info.assert_called_once()

    @patch("tickets.tasks.logger")
    @patch("tickets.tasks.requests.post")
    @patch("tickets.tasks.render_to_string", return_value="<p>Hello</p>")
    @patch.object(send_email_task, "retry", side_effect=RuntimeError("retry called"))
    def test_send_email_task_retries_when_brevo_returns_error(self, mock_retry, _mock_render, mock_post, mock_logger):
        mock_post.return_value = SimpleNamespace(status_code=500, text="server error")
        with self.assertRaisesMessage(RuntimeError, "retry called"):
            send_email_task.run("user@example.com", "Subject")
        mock_logger.error.assert_called_once()
        mock_retry.assert_called_once()

    @patch("tickets.tasks.logger")
    @patch("tickets.tasks.render_to_string", side_effect=ValueError("template broken"))
    @patch.object(send_email_task, "retry")
    def test_send_email_task_does_not_retry_non_request_errors(self, mock_retry, _mock_render, mock_logger):
        with self.assertRaisesMessage(ValueError, "template broken"):
            send_email_task.run("user@example.com", "Subject")
        mock_logger.error.assert_not_called()
        mock_retry.assert_not_called()
