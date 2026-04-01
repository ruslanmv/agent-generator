"""Tests for the NL parser."""

import pytest

from agent_generator.utils.parser import parse_natural_language_to_workflow


def test_basic_parsing():
    wf = parse_natural_language_to_workflow("Research the market. Write a report.")
    assert len(wf.tasks) == 2
    assert len(wf.agents) == 1
    assert len(wf.edges) == 1


def test_single_sentence():
    wf = parse_natural_language_to_workflow("Build a chatbot")
    assert len(wf.tasks) == 1
    assert len(wf.edges) == 0


def test_empty_input():
    with pytest.raises(ValueError, match="No tasks"):
        parse_natural_language_to_workflow("")


def test_sequential_edges():
    wf = parse_natural_language_to_workflow("Step one. Step two. Step three.")
    assert len(wf.tasks) == 3
    assert len(wf.edges) == 2
    assert wf.edges[0].source == "task_1"
    assert wf.edges[0].target == "task_2"
    assert wf.edges[1].source == "task_2"
    assert wf.edges[1].target == "task_3"
