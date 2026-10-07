# HW4 — AI Prompts Log

Log of the prompts typed to the AI coding assistant (Claude Code) while completing Homework 4.
Prompts are recorded verbatim, grouped by problem, in the order they were typed. When a follow-up was needed, one sentence explains what the first prompt was missing.
The running site, database writes and screenshots are the evidence of the work.

---

## Setup

**Prompt 1:**
> we are going to do the homework 4 for the course. So we will work in the HW4 folder

**Prompt 2 (project context):**
> Before starting I'm going to give you a little bit of context. In the homework a store needs a real customer website with a helpful chatbot, so throughout all the problems we will build a React+Vite TypeScript front end and a Python Fast API backend whose brain is a Pydantic AI agent. The idea is that shoppers should be able to browse, create account, chat aout merch and see matching items appear on the page, and get honest answers about price and stock from a local database. We will do problem by problem, so dont do nothing yet, this is just context

---

## Problem 1 — Vibe Coder Prompts

**Prompt 1:**
> Perfect, so we are going to start creating AI_prompts.md and keeping it updated as we work. This file is the log of what I'll typed to you. The idea is to put one section for each problem, and each section must include the problem number and title, at least one prompt I typed in my own words as much as possible, one foloow-up prompt if I needed it (and one sentence of what was lacking after the first prompt). Our running site, database writes and screenshots will be our evidence, so we dont need an extra proof essay beyond these prompts. This is Problem 1, called Vibe coder prompts

---

## Problem 2 — Analyze the Database

**Prompt 1:**
> Now Problem 2, it title is Analyze the database. So please look at the database data/campus_customs.db and understand the fields of each table. At a minimum you should understand catalogue, inventory and users. So please start the file output/harness.md, writing down each table and its fields, and one short line on why each field matters for the shop or the chatbot. We will keep growing this harness file in later problems (models, tools, safety and specs)

---

## Problem 3 — Build the Campus Customs Website

**Prompt 1:**
> Problem 3 is called, build the campus customs website. So, scaffold a react+vite+typescript front end for campus customs. Put a nav bar at the top that links to the main pages: Home, Products, about us, log in, create account. Now pull Campus Customs style wording from their webpage (https://yalebulldogblue.com/) for the Home, and for About Us, but write these pager with your own voice, meaning, please do not copy the original site text. It is important that on the products page, you show product images from the catalogue. For this, use the image paths in the data base. Also, each product should have basic product info like the name, price and short description. Make each product open a singl item page (large image on one side, full product text on the other - including description, price, sizes/stock whn you have them). Clicking a card on Products should take the shopper there. Also add a chat interface in th bottom right of the site, like a floating chat panel is fine. It doesnot need to talk to an agen yet, a stube that will call your backend later is enough for this problem. You will need a small API soon to read the database. It is fine to start a simple fastAPIapp in backend/main.py just to serve products and images, then grow it into the agent bbackend in problem 5

---

## Problem 4 — Create Account and Login

**Prompt 1:**
> Nice, now problem 4's title is Create account and login. Help me building a normal create-account/login flow. In create account ask for the first name, last name, email, password, and confirm password. In the login, email and passwords. New accounts go into the users table. Make sure to store passwords sucrely so hackers (either humans or AI) cannot access them. The seed database already has a test user you can use while building. email test is: test@campuscustoms.yale.edu, password passwprd. The idea is that you confirm if you can log in that user, and that a brand-new account you create also works. Update output/harness.md with how auth works (what you store for a user and how passwords are protected)

---

## Problem 5 — PydanticAI Agent Backend

**Prompt 1:**
> Problem 5 is called PydanticAI agent backend. Build the shop chatbot as a Pydantic AI agent behinf FastAPI, plugged into your front-end chat widget. Put the API app in backend/main.py that is the file you run with Uvicorn. Keep the agent as these four files next to it, similar to what we did in HW3: backend/prompts/prompt.md that is the system prompt that you will grow this same file later, backend/agent.py that is agent entry/wiring, backend/tools.py that are tools the agent can call, backend/models.py pydantic/pydanticAI structured types. In main.py, expose a chat route so a message from the website returns a reply from the agent and whatever else you need for products/auth. You will need your AI model API key for the agent. Put campus customs voice and safety basics into prompts/prompt.md taking into account that you will expand tools and safety later. Start or update types in models.py for chat replies/product cards as needed. In output/harness.md note how the front end talks to FastAPI and how the agent is loaded (prompt file+model). Make sure the backend runs from the backend/ folder like this: uvicorn main:app --reload --port 8000

---

## Problem 6 — Tools: Product Info and Stock

**Prompt 1:**
> Great work, problem 6 is called tools:product info and stock. Here the idea is to give the agent tools that look up real information from campus_customs.db: Products description, price, how many are in stock (by size when the customer asks). The agent must use the database, it should not invent prices or quantities. If a size is out of stock, say so clearly. Expand propmpts/prompt.md so the agent knows to call these tools for price and stock questions. Add or update return types in models.py. In output/harness.md, list each tool and explain which model fields you chose for lookup results and why

---

## Problem 7 — Chat Search That Updates the Page

**Prompt 1:**
> Problem 7 is called Chat search that updates the page. Now we will add a neat feature to the site. When a customer asks about a type of item, like for example what hoodies do you have? the agent should search the catalogue and the website should dynamically show those matching items as product cards, including their image, name, price and short info. This is an API contract: the agent returns structured product matches and then the front end renders them on the website. it looks really cool. Adter the dynamic product cards are loaded by our new feature, make sure the same singleitem page behavior we built in problem 3 still works: each product card, including the ones the chat just put on the page, should still open that detail view (large image + full info) when clicked. Update prompts/prompt.md and output/harness.md so it is clear how search results reach the page

---

## Problem 8 — Customer Memory

**Prompt 1:**
> Perfect. Problem 8 title is customer memory. The idea for this problem is that when a shopper logs in, you should save their chat history in the database in an appropriate table and reload it when they return. The agent should know who is chatting (name and email) put that info in agent deps (or an equivalent clear pattern) and/or tools the agent can call. Also pass enough page context that if someone is on a product page and asks "do you have this in pink?" the agent know which item they mean. Hint: you can put code into the agent context. The idea is that guests can still chat, bbut history only needs to persist for logged-in users. Document in output/harness.md how use chat history is stored, what customer fields the agent sees, and how page context is passed

---

## Problem 9 — Usability Improvements

**Prompt 1:**
> Perfect, that's great. Uh, we're now going to go to problem nine, which is called usability improvements. Uh, the idea in this one is that we start to choose different improvements and implement them. So we're now in this phase because uh, now the core shop works. So the idea is just to improve it. So they, we have uh, first um, to define two front end usability improvements. Uh, these ones are things that make the site look better and make it easier to use. And we have to now choose also two agent backend usability improvements. This type of improvements are things that make the agent output better, more accurate or safer. This could be either new agent tools or things that make the agent run faster or cheaper. So what I'm thinking is, uh, I think it would be a great idea if you give me like four options for each, four options for front end, four options for agent and back end for me to pick up and decide which one's better. After that, I'm going to give you uh, something like a, a prompt that is related with problem nine also.

**Selection (picked from the 4 + 4 options the assistant proposed):**
> Frontend: Size picker + stock badges, Mobile & accessibility polish. Agent/backend: Price/stock fact-checker, Streaming + live tool status.

**Prompt 2:**
> So now that I now that we have decided uh, which are the changes, it is important for you to write in output/usability.md before or as you build. The idea is that for each of the improvements, you have to write what you added and why it helps a campus custom shopper or the business. It is important not to make really, really long essays I think that the main point can be described in just one paragraph. Then make sure that all improvements actually show up in the running app taking into account that graders will read the write-up and look for the features there. customer shopper or the business. It is important not to make really, really long essays. I think that the main point can be described in just one paragraph. Then make sure that all improvements actually show up in the running app, greater, taking into account that graders will read the write-up and look for the features there.

---

## Problem 10 — Style the Website

**Prompt 1:**
> Perfect. So now we're going for problem 10. It is called style the website. First, I'm going to tell you a little bit of context. Then I'm going to mention oh. , my different ideas for this. So the context is that in this problem, we should add creative design to the site feels a little bit more real. Like the campus custom storefront so we need to add or change things around the fonts the color the hierarchy the motion the product presentation and general the chat, feel the idea is that if we are more imaginative and more innovative , we're going to have more points. So the first thing I'm thinking is in the home page, it is key that you, you have really engaging images and something really big like I'm seeing a new can maybe search something like around Abercrombie or Ralph Lauren those brands really start with something engaging with images that are engaging before having all the storefront right in your face so that would be the first thing we could change. have really engaging images and something really big. Like I'm saying, and you can maybe search something like around Abercrombie or Ralph Lauren. Those brands really start with something engaging with images that are engaging. before having all the storefront right in your face. So that would be the first thing we could change. The other thing is that even though the blue is quite cool, uh, I think we could do something a little bit different. Of course, staying, staying in that blue, that is really important for Yale. But I feel that at the end, you went really to the default font and to the default blue that you have. I think you can, yeah, do a little, uh, something a little bit different there. I don't know which is the, um, the font you used, but you can change it to something more engaging and more for e-commerce. All of this has to be written in output/design.md. Where you have to include what you changed and why it should help customer stick around and buy, keeping it concrete and short. if you have other two ideas we can iterate them before you actually doing them

**Selection (answers to the assistant's two questions):**
> Hero images: Real Yale campus photos. Extra idea: Handsome Dan chat persona.

---

## Problem 11 — Test the App (app check)

**Prompt 1:**
> Nice, perfect. So now we're going uh, to problem 11. The idea is that I test the app you already made. So, all the comments and screenshots should be documented in output/app_check.html (a page you can double-click open). The first I'm going to check is the inventory level. as you see in the first two screenshots, the chatbot tells uh, Stock that it's the sum of all the sizes meanwhile when I check the specific size that I wanted and that I asked in the chatbot it's way less the stock than the one that's mentioned in the chat. bot tells a uh, stock that it's like complete. That it's the sum. The sum of all the sizes. Meanwhile, when I check the specific size that I wanted and that I asked in the chatbot, it's way less this stock than the one that's mentioned in the chat. In the third screenshot, I'm checking the dynamic search result cards appearing after a category question. And I think it's okay. Like, in the chat that is also included in the first screenshot, it's really interesting and it's really upfront, the products. And when I click to see a little bit more of detail, it's really easy to get and to see the products. So as I mentioned before, try to make the HTML easy to grade. Heading for each check, screenshot, and one or two sentences on what each of the screenshots looks like. You can also think and maybe complement what I'm saying. The idea is that you put this screenshot images in output/app_check_images/ and link them from app_check.html with relative paths (for example app_check_images/inventory.png)

**Follow-up 1:**
> yes, trim the black bars on the photos

*What was lacking after the first prompt:* the app check only documented the black bars baked into 73 of the 102 product photos as an observation, so fixing them needed an explicit go-ahead.

---

## Problem 12 — Audit Trail, Safety, Finish Harness

**Prompt 1:**
> Perfect, now problem 12. It's title is outdated trail safety finish hardness. The idea in this one is to keep an append only output/audit_trail.json of agent loop activity including time tool name short args and results stop reason and like all the things we should understand from from this agent loop activity the idea is not to wipe it, including time, tool, name, short arguments, and results, stop, reason, and like all the things we should understand from, from this agent loop activity. The idea is not to wipe up, wipe it between runs. And also it's important to think on some safety rules to give the agent and put them in prompts/prompt.md. Also finish output/harness.md so it is clear how the system works. Including model fields in models.py and why you chose them, tools and anilities, safety rules, specifications like loop limits, result caps, models, how to run front and back etc

---

## Problem 13 — Push to GitHub and Submit the URL

**Prompt 1:**
> Perfect. We're now going to the last problem. It's problem 13. It's called push to GitHub and submit the URL. So the idea is to put the code in a folder named hw4 HW4. And push it to a public GitHub repository. Do not put your real .env, campus_customs.db, or product images in the github repo. Use .gitignore. Include .env.example with placeholders only. the expected file layour is attached. Therefore, the agent itself is four files under backend/: prompts/prompt.md, agent.py, tools.py and models.py. README.md should explain how to run the front and back end after placing the data pack

---
