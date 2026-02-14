export interface CurriculumTask {
  id: number;
  task_description: string;
  reasoning: string;
  status: "pending" | "completed";
  priority: "high" | "medium" | "low";
  created_at: string;
}
