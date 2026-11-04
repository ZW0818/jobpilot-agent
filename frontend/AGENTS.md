# Frontend requirements

Before changing this frontend, read [DESIGN.md](DESIGN.md). Its design direction is adapted from [Taste Skill](https://github.com/Leonxlnx/taste-skill), specifically its app-screen rules.

- Treat JobPilot as a working app, not a marketing landing page. Keep the existing React/Vite stack and the analysis, chat, report and download contracts.
- Use the shared neutral tokens, 8px panel / 6px control radii, one data hue, readable Chinese system typography and aligned tabular figures.
- Avoid gradients, glass, glows, large card shadows, decorative badges, fake scores and invented usage statistics.
- Keep input labels, empty/loading/error/disabled states, visible keyboard focus, arrow-key report tabs and reduced-motion support.
- Preserve material and conversation state when switching views. Never put API Keys or private resume contents into source files or debug logs.
- Verify the production build at 1440, 768 and 390 pixels. Inspect screenshots and click through navigation, inputs, report tabs and downloads. Report checks honestly if a browser is unavailable.
