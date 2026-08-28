export type Thread = {
  id: string;
  messages: Array<{ role: string; content: string }>;
};

const threads = new Map<string, Thread>();

export function loadThread(id: string): Thread {
  return threads.get(id) ?? { id, messages: [] };
}

export function saveThread(thread: Thread): void {
  threads.set(thread.id, thread);
}
