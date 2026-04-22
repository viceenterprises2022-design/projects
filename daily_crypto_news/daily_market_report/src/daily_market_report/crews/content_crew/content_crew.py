from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task


@CrewBase
class MarketReportCrew:
    """Heavy mode: draft + risk review."""

    agents: list[BaseAgent]
    tasks: list[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def lead_researcher(self) -> Agent:
        return Agent(config=self.agents_config["lead_researcher"])  # type: ignore[index]

    @agent
    def risk_reviewer(self) -> Agent:
        return Agent(config=self.agents_config["risk_reviewer"])  # type: ignore[index]

    @task
    def draft_report_task(self) -> Task:
        return Task(config=self.tasks_config["draft_report_task"])  # type: ignore[index]

    @task
    def review_report_task(self) -> Task:
        return Task(
            config=self.tasks_config["review_report_task"],  # type: ignore[index]
            context=[self.draft_report_task()],
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )


@CrewBase
class MarketReportCrewLite:
    """Moderate mode: single-pass JSON draft only."""

    agents: list[BaseAgent]
    tasks: list[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks_lite.yaml"

    @agent
    def lead_researcher(self) -> Agent:
        return Agent(config=self.agents_config["lead_researcher"])  # type: ignore[index]

    @task
    def draft_report_task(self) -> Task:
        return Task(config=self.tasks_config["draft_report_task"])  # type: ignore[index]

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
