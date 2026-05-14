import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);

const BLOCKED_PATTERNS = [
  "rm -rf",
  "sudo",
  "shutdown",
  "reboot",
  "mkfs",
  ":(){:|:&};:",
  "dd ",
];

export async function safeExecute(
  command: string,
  cwd: string = "./workspace"
) {
  for (const blocked of BLOCKED_PATTERNS) {
    if (command.includes(blocked)) {
      throw new Error(
        `Blocked dangerous command: ${blocked}`
      );
    }
  }

  // Allow only manim-related commands
  const allowed =
    command.startsWith("manim") ||
    command.startsWith("python") ||
    command.startsWith("ls") ||
    command.startsWith("find") ||
    command.startsWith("ffmpeg") ||
    command.startsWith("cat") ||
    command.startsWith("echo") ||
    command.startsWith("mkdir");

  if (!allowed) {
    throw new Error(
      "Only limited commands are allowed"
    );
  }

  return execAsync(command, {
    cwd,
  });
}