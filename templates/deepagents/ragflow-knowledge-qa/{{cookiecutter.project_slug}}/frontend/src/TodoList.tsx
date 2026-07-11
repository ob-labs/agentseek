import type { ReactNode } from "react";

export type TodoStatus = "pending" | "in_progress" | "completed";

export type TodoItem = {
  content: string;
  status: TodoStatus;
};

function statusLabel(status: TodoStatus): string {
  switch (status) {
    case "completed":
      return "done";
    case "in_progress":
      return "active";
    default:
      return "queued";
  }
}

export default function TodoList({ todos }: { todos: TodoItem[] }): ReactNode {
  if (todos.length === 0) return null;

  const completedCount = todos.filter((todo) => todo.status === "completed").length;
  const progress = Math.round((completedCount / todos.length) * 100);

  return (
    <section className="todo-panel" aria-label="Agent plan">
      <div className="todo-panel__header">
        <div>
          <p className="todo-panel__eyebrow">Live progress</p>
          <h2 className="todo-panel__title">Agent plan</h2>
        </div>
        <div className="todo-panel__summary">
          <strong>{progress}%</strong>
          <span>{completedCount}/{todos.length} completed</span>
        </div>
      </div>

      <ol className="todo-list">
        {todos.map((todo, index) => (
          <li key={`${todo.content}-${index}`} className={`todo-list__item todo-list__item--${todo.status}`}>
            <span className="todo-list__index">{index + 1}</span>
            <span className="todo-list__content">{todo.content}</span>
            <span className={`todo-list__status todo-list__status--${todo.status}`}>
              {statusLabel(todo.status)}
            </span>
          </li>
        ))}
      </ol>
    </section>
  );
}
