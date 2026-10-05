# {{title}}

Write what this automation must do, in plain language (Thai or English). This file is the source for `flow.md`: an AI assistant reads it and writes the flow, and you review the result. Replace every `<...>` and delete the hints you do not need.

## Goal

<One or two sentences: what the bot achieves and for whom. For example: "Collect yesterday's closing prices for my watch list and email them to the finance team every weekday at 08:00.">

## Steps

1. <First thing the bot does, for example: open https://example.com/quotes>
2. <What it reads, clicks, types, or downloads>
3. <What it does with the data: filter, group, calculate>
4. <Where the result goes: a CSV or Excel file, an email, an API>

## Settings that must change without editing the flow

<Values a person may change later. They go into config/config.json, never into flow.md.>

- <URL(s)>
- <Lists such as stock symbols, currencies, customers>
- <Dates or periods>
- <Output file paths>
- <Email recipients>

## Secrets

<Passwords, API keys, or tokens the bot needs. They go into .env (copy .env.example), never into config.json or flow.md.>

- <none>

## Output

<File name and format, columns, grouping and sort order, or the message to send.>

## Errors and exceptions

<What should happen when something goes wrong. Technical problems (site slow, file locked) are usually retried; business problems (no data, invalid values) should stop the flow with a clear message.>

- <For example: if the site does not respond, retry twice, then stop>
- <For example: if a symbol has no data, stop and say which one>

## Schedule

<When it runs: by hand, every weekday at 08:00, when a file arrives in a folder.>
