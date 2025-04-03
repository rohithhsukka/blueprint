import os
import io
import datetime
from flask import Flask, request, send_file, jsonify
from openai import OpenAI
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.lib.units import inch

# --- Configuration ---
load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)
openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set.")

# It's better to initialize the client once
try:
    client = OpenAI(api_key=openai_api_key)
except Exception as e:
    raise RuntimeError(f"Failed to initialize OpenAI client: {e}")


# --- SOP Data Storage ---
# (Storing SOPs directly here for simplicity in a single file)
# In a larger app, these might come from a database or config files.
SOP_DATA = {
    "Ideal Client Profile (ICP) Definition": """
    **Objective:** To deeply understand and document the target audience(s) for the EdTech client's products/services to inform all subsequent marketing efforts.
    **Timeline:** 1-2 Weeks
    **Checklist:**
    - Client Kick-off Meeting (Understand current view, gather data, define problem)
    - Market Research (Competitor analysis, industry trends, online communities)
    - Data Analysis (Website/app analytics, sales data, CRM data)
    - Qualitative Research (Surveys, interviews with customers/prospects/stakeholders)
    - Synthesize Findings (Identify demographics, psychographics, pain points, watering holes)
    - Create Buyer Personas (Develop 2-4 detailed personas)
    - Validation & Sign-off (Present to client, revise, get approval)
    - Documentation (Store finalized ICPs/Personas)
    """,
    "Brand Building & Brand Assets": """
    **Objective:** To establish a clear, compelling, and consistent brand identity that resonates with the target EdTech audience and differentiates the client.
    **Timeline:** 2-4 Weeks
    **Checklist:**
    - Brand Discovery Workshop (Mission, Vision, Values, USP, Archetype, Voice)
    - Competitor Brand Analysis (Visuals, messaging, differentiation opportunities)
    - Messaging Framework Development (Core message, value props, elevator pitch)
    - Visual Identity Development (Logo, color palette, typography, imagery style)
    - Core Brand Asset Creation (Templates: biz card, letterhead, presentation, email sig, social profiles)
    - Brand Guidelines Document (Compile all elements, usage rules)
    - Client Review & Approval (Present concepts, iterate, get sign-off)
    - Asset Delivery & Storage (Deliver files, store centrally)
    """,
    "Creating Social Presence & Positioning": """
    **Objective:** To establish and optimize the client's presence on relevant social media platforms, positioning them effectively.
    **Timeline:** 1-2 Weeks (Initial Setup & Strategy)
    **Checklist:**
    - Platform Selection (Based on ICP watering holes: LinkedIn, FB, IG, TikTok, YouTube etc.)
    - Profile Creation & Optimization (Consistent handles, optimized bio, logo/banners, links)
    - Content Strategy Outline (Content pillars: Tips, Spotlights, News, Success Stories, Q&A; Format mix; Frequency)
    - Positioning Strategy (Define relative position vs. competitors)
    - Initial Content Calendar (Plan first 2-4 weeks)
    - Hashtag Strategy (Research branded, community, niche hashtags)
    - Client Review & Approval (Present strategy, profiles, calendar)
    - Go Live & Initial Monitoring
    """,
    "Creating Web Presence (Website Building)": """
    **Objective:** To design, build, and launch a user-friendly, conversion-focused website as the central online hub.
    **Timeline:** 4-12 Weeks (Depending on complexity)
    **Checklist:**
    - Define Website Goals & Strategy (Lead gen, sales, info hub; User paths; Integrations needed)
    - Sitemap & Architecture (Logical structure, navigation plan)
    - Platform & Hosting Selection (CMS: WordPress+LMS, Teachable/Thinkific, custom; Reliable hosting)
    - Wireframing & Prototyping (Low/high fidelity mockups, mobile-responsive design)
    - Content Gathering & Creation (Collect/write copy, images, videos, course details, testimonials)
    - Website Development (Build based on designs, implement features, integrate plugins)
    - On-Page SEO Implementation (Keywords, titles, metas, headings, alt text, structure, speed)
    - Integration Setup & Testing (Forms, email, payment, CRM, analytics)
    - Quality Assurance & Testing (Cross-browser/device, links, speed, forms, responsiveness)
    - Client Training (If applicable)
    - Pre-Launch Checklist (Final SEO, favicon, SSL, backup, redirects, tracking verification)
    - Launch & Post-Launch Monitoring (Deploy, monitor analytics, submit to search engines)
    """,
    "Consistent Blog Writing": """
    **Objective:** To regularly create valuable, SEO-optimized blog content to attract the target audience, build authority, and support lead generation.
    **Timeline:** Ongoing (Cycle per post: ~1-3 days)
    **Checklist:**
    - Content Strategy & Keyword Research (ICP needs, goals, keywords, competitor analysis, pillars)
    - Content Calendar Planning (Monthly schedule, topics, keywords, CTAs)
    - Topic Ideation & Outlining (Angle, title, detailed outline, H2s/H3s, links, CTA placement)
    - Writing & Drafting (Engaging, valuable, clear content for audience; Brand voice)
    - Editing & Proofreading (Grammar, spelling, clarity, flow, accuracy)
    - SEO Optimization (Keyword integration, title/meta, headings, internal/external links, image alt text)
    - Visuals & Formatting (Relevant images/infographics, web readability)
    - Call-to-Action (CTA) Integration (Clear, relevant CTAs linking correctly)
    - Client Approval (If required)
    - Publishing (Upload to CMS, categories/tags, featured image)
    - Promotion (Share on social, email newsletter, outreach)
    - Performance Tracking (Traffic, time on page, bounce rate, keyword rankings, conversions)
    """,
    "Social Media Content Generation (Video & Written)": """
    **Objective:** To consistently create and publish engaging written and video content across selected platforms aligned with brand strategy.
    **Timeline:** Ongoing (Daily/Weekly activity)
    **Checklist:**
    - Content Calendar Management (Weekly/Monthly plan: topic, format, caption, hashtags, CTA)
    - Written Content Creation (Engaging captions, platform best practices, CTAs, text posts, video scripts)
    - Visual Content Creation (Graphics: Canva/Adobe; Stock photos/client images; Infographics, carousels; Optimize dimensions)
    - Video Content Creation (Pre-prod: script/storyboard; Prod: filming/recording; Post-prod: editing, branding, captions, music; Format optimization)
    - Content Review & Approval (Internal quality check, client approval if needed)
    - Scheduling & Publishing (Use tools like Buffer/Hootsuite; Manual publishing for some formats)
    - Community Management & Engagement (Monitor daily, respond promptly, proactive engagement)
    - Performance Monitoring & Reporting (Track metrics per platform, analyze top content, report insights)
    """,
    "Ideate Revenue Streams from Content": """
    **Objective:** To strategically leverage content to create new or optimize existing revenue streams.
    **Timeline:** 1-2 Weeks (Initial Ideation), Ongoing (Refinement)
    **Checklist:**
    - Content Audit & Performance Analysis (Review inventory, identify popular topics/formats)
    - ICP & Offer Alignment (Revisit needs, analyze current offerings, identify gaps)
    - Brainstorm Monetization Opportunities (Lead Magnets, Low-Ticket Offers, Content Upsells, Webinar entries, Memberships, Direct promotion, Affiliate)
    - Assess Feasibility & Potential (Estimate effort vs. ROI, prioritize)
    - Develop Offer Concepts (Outline deliverables, value prop, pricing, funnel fit)
    - Client Presentation & Discussion (Present ideas, rationale, decide collaboratively)
    - Action Plan (Outline steps for approved ideas)
    - Documentation (Record process and decisions)
    """,
    "Specific Funnel Building (Price Point Based)": """
    **Objective:** To design, build, and test marketing funnels tailored to the offer's price point to guide prospects towards conversion.
    **Timeline:** 2-6 Weeks per funnel
    **Checklist:**
    - Define Funnel Goal & Offer (Specific objective, product, ICP segment, price point)
    - Select Funnel Type (Low-Ticket: Direct Sale; Mid-Ticket: Webinar/Workshop; High-Ticket: Application/Call)
    - Map Funnel Stages & User Journey (Outline steps from awareness to post-conversion)
    - Technology & Tool Setup (Landing Page Builder, Email Marketing, Webinar Platform, Scheduler, Payment, CRM, Analytics)
    - Content Creation for Funnel Assets (Copywriting: Ads, Pages, Emails; Visuals: Designs, graphics, slides; Webinar content; Application Qs)
    - Build Funnel Pages & Automations (Build pages, set up email sequences/rules, integrate tools)
    - Tracking Implementation (Install pixels, set up goals/events in Analytics/Ads, use UTMs)
    - Testing (Full user flow, forms, emails, integrations, payments, links, devices/browsers)
    - Pre-Launch Review (Check all assets, verify tracking, get client sign-off)
    - Launch Funnel (Activate automations, make pages live, start traffic)
    - Initial Monitoring (Check analytics frequently for issues)
    """,
    "Traffic Generation (Performance, Influencer, Organic)": """
    **Objective:** To drive qualified traffic from multiple sources into the defined marketing funnels.
    **Timeline:** Ongoing
    **Checklist:**
    - Define Traffic Goals & Budget (Volume needed, budget allocation, target CPL/CPA)
    - Performance Marketing (Paid Ads) Setup & Management (Platform choice, campaign structure, audience targeting, keyword research, ad creative dev, landing page alignment, bidding/budgeting, tracking setup, launch, ongoing optimization: A/B tests, bid/budget adjustments, scaling/pausing)
    - Influencer Marketing Execution (Identification/vetting, outreach/negotiation, campaign brief, content review, tracking links/codes, relationship mgmt)
    - Organic Marketing Execution (SEO: technical, on-page, content, backlinks; Social Media: content calendar, engagement; Email Marketing: newsletters, nurturing, promotions)
    - Traffic Allocation & Monitoring (Track sources via UTMs, analyze channel performance, adjust budget/effort based on ROI)
    """,
    "KPI Tracking & Funnel Optimization": """
    **Objective:** To continuously monitor KPIs, analyze funnel performance, identify bottlenecks, and implement data-driven optimizations to maximize ROI.
    **Timeline:** Ongoing (Daily/Weekly/Monthly analysis cycles)
    **Checklist:**
    - Define Key Performance Indicators (KPIs) (Business: ROI, CAC, CLTV; Traffic: Sessions, CTR, CPC; Engagement: Bounce Rate, Session Duration; Funnel Specific: CVRs, CPL, Rates - Reg/Attend/Apply/Book/Close; Sales: CVR, AOV, ROAS, Revenue)
    - Setup Tracking & Reporting Tools (GA Goals/Events, Ad Pixels, CRM, Dashboard: Data Studio/Spreadsheet)
    - Establish Reporting Cadence (Daily checks, Weekly analysis, Monthly deep dive, Quarterly review)
    - Data Analysis & Interpretation (Compare vs. history/goals, identify bottlenecks, segment data, analyze creative/LP performance)
    - Hypothesis & A/B Testing (Formulate hypotheses, prioritize tests, systematically test elements, ensure statistical significance)
    - Implement Winning Variations (Document results, roll out winners, pause losers)
    - Iterate & Refine (Continuously repeat cycle, apply learnings, stay updated)
    - Client Reporting & Communication (Regular reports: KPIs, insights, tests, results, recommendations; Focus on ROI; Transparency)
    """
}


# --- Helper Functions ---

def format_text_for_reportlab(text):
    """ Basic formatting conversion for ReportLab Paragraphs """
    text = text.replace('\n', '<br/>')
    # Basic bold handling - assumes **text** format from SOPs
    text = text.replace('**', '<b>').replace('**', '</b>', 1) # Replace pairs
    # Handle bullet points (simple conversion)
    text = text.replace('- ', '<bullet>&bull;</bullet> ')
    return text

def generate_ai_blueprint(company_details):
    """ Generates the blueprint text using OpenAI """
    prompt = f"""
    Act as a professional Performance Marketing Consultant specializing in EdTech.
    You are generating a customized Performance Marketing Blueprint for a potential client.
    This blueprint should outline the proposed strategy and execution steps, demonstrating clear value and a structured approach based on standard best practices (SOPs).
    The goal is to convince the client to purchase these performance marketing services.

    Client Company Details:
    - Company Name: {company_details.get('company_name', 'N/A')}
    - Product/Service: {company_details.get('product_service', 'N/A')}
    - Target Audience (Brief): {company_details.get('target_audience', 'N/A')}
    - Key Business Goal: {company_details.get('business_goal', 'N/A')}
    - Website (Optional): {company_details.get('website', 'N/A')}
    - Current Marketing Efforts (Brief): {company_details.get('current_marketing', 'N/A')}

    Based on these details, create a Performance Marketing Blueprint. Structure the blueprint using the following Standard Operating Procedures (SOPs) as sections.
    For EACH SOP section, do not just list the checklist. Instead, briefly explain HOW this phase will be specifically approached and tailored for THIS client ({company_details.get('company_name', 'The Client')}), considering their product, audience, and goals. Highlight the importance and expected outcome of each phase for their specific business. Maintain a professional, confident, and action-oriented tone.

    Here are the SOPs to structure the blueprint around:
    --- SOP SECTIONS START ---
    """

    # Append SOP data to the prompt, ensuring the AI knows the structure
    for title, details in SOP_DATA.items():
        # Extract objective from details (assumes format "**Objective:** <text>")
        objective = details.split("**Objective:**")[1].split("**Timeline:**")[0].strip()
        
        # Add section to prompt with title and objective
        prompt += f"\n\n## {title}\nObjective: {objective}\n"
        prompt += f"(Explain the specific approach and strategy for {company_details.get('company_name')} based on this objective. Consider their product/service, target audience, and goals.)\n"

    prompt += """
    --- SOP SECTIONS END ---

    Concluding Remarks: End with a brief summary statement about the holistic approach and focus on achieving the client's key business goal through measurable results and ROI.

    Generate ONLY the blueprint text, formatted clearly with headings for each SOP section.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # Or "gpt-3.5-turbo" or other suitable model
            messages=[
                {"role": "system", "content": "You are a professional Performance Marketing Consultant specializing in EdTech generating a client blueprint."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7, # Adjust for creativity vs predictability
            max_tokens=3000  # Adjust based on expected length
        )
        # Defensive coding: Check if response structure is as expected
        if response.choices and len(response.choices) > 0:
             blueprint_text = response.choices[0].message.content.strip()
             return blueprint_text
        else:
             print("Warning: OpenAI response structure unexpected or empty.")
             return "Error: Could not generate blueprint due to unexpected API response."

    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        # Provide a more informative error message if possible
        return f"Error: Failed to generate blueprint using AI. Details: {str(e)}"


def create_pdf_blueprint(company_name, blueprint_text):
    """ Creates the PDF document in memory """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            leftMargin=inch, rightMargin=inch,
                            topMargin=inch, bottomMargin=inch)
    styles = getSampleStyleSheet()

    # Custom Styles (Optional)
    styles['h1'].alignment = TA_CENTER
    styles['h1'].fontSize = 18
    styles['h2'].fontSize = 14
    styles['h2'].spaceBefore = 12
    styles['h2'].spaceAfter = 6
    styles['Normal'].alignment = TA_JUSTIFY
    styles['Normal'].fontSize = 11
    styles['Normal'].leading = 14 # Line spacing

    story = []

    # Title
    story.append(Paragraph(f"Performance Marketing Blueprint", styles['h1']))
    story.append(Paragraph(f"Prepared for: {company_name}", styles['h1']))
    story.append(Paragraph(f"Date: {datetime.date.today().strftime('%B %d, %Y')}", styles['Heading3']))
    story.append(Spacer(1, 0.5*inch))

    # Introduction (Optional - could be generated by AI too)
    intro_text = f"This document outlines a proposed performance marketing strategy tailored for {company_name}, focusing on achieving your business goals through a data-driven, holistic approach. We will leverage the following phases to build a robust marketing engine:"
    story.append(Paragraph(intro_text, styles['Normal']))
    story.append(Spacer(1, 0.2*inch))

    # Process Blueprint Text
    # Simple split by heading marker used in the prompt (##)
    sections = blueprint_text.split('## ')
    first_section = True
    for section in sections:
        if not section.strip():
            continue

        lines = section.strip().split('\n', 1)
        title = lines[0].strip()
        content = lines[1].strip() if len(lines) > 1 else ""

        # Add space before new sections except the first actual one
        if not first_section:
             story.append(Spacer(1, 0.3*inch))
        else:
             # The first part might be an intro from the AI before the first '##'
             if title not in SOP_DATA: # Check if it's a real SOP title
                  story.append(Paragraph(format_text_for_reportlab(section), styles['Normal']))
                  continue # Skip adding it as a heading if it's not an SOP title
             first_section = False


        story.append(Paragraph(title, styles['h2']))
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph(format_text_for_reportlab(content), styles['Normal']))


    # Add Page Breaks if needed (SimpleDocTemplate handles flow automatically)
    # story.append(PageBreak())

    try:
        doc.build(story)
        buffer.seek(0)
        return buffer
    except Exception as e:
        print(f"Error building PDF: {e}")
        # Return None or raise exception to handle it in the route
        return None


# --- Flask Route ---

@app.route('/generate_blueprint', methods=['POST'])
def generate_blueprint_endpoint():
    """
    API endpoint to generate the performance marketing blueprint PDF.
    Expects form data: company_name, product_service, target_audience, business_goal,
                       website (optional), current_marketing (optional)
    """
    if not request.is_json:
         # Fallback for form data if not JSON
         if not request.form:
             return jsonify({"error": "Missing form data or JSON payload"}), 400
         company_details = request.form.to_dict()
    else:
        company_details = request.get_json()

    # Basic Validation
    required_fields = ['company_name', 'product_service', 'target_audience', 'business_goal']
    if not all(field in company_details and company_details[field] for field in required_fields):
        missing = [field for field in required_fields if not company_details.get(field)]
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    # 1. Generate Blueprint Text using AI
    print("Generating AI blueprint...")
    blueprint_text = generate_ai_blueprint(company_details)

    if blueprint_text.startswith("Error:"):
        print(f"AI Generation Failed: {blueprint_text}")
        return jsonify({"error": blueprint_text}), 500

    print("AI Blueprint generated successfully.")

    # 2. Create PDF from the generated text
    print("Creating PDF document...")
    pdf_buffer = create_pdf_blueprint(company_details.get('company_name'), blueprint_text)

    if pdf_buffer is None:
         print("PDF Generation Failed.")
         return jsonify({"error": "Failed to generate PDF document."}), 500

    print("PDF created successfully.")

    # 3. Send PDF back to the user for download
    safe_company_name = "".join(c for c in company_details.get('company_name', 'Client') if c.isalnum() or c in (' ', '_')).rstrip()
    filename = f"Performance_Blueprint_{safe_company_name}_{datetime.date.today()}.pdf"

    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )

# Basic route for testing if the server is up
@app.route('/')
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Performance Marketing Blueprint Generator</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                max-width: 800px;
                margin: 40px auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                background-color: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            h1 {
                color: #2c3e50;
                text-align: center;
                margin-bottom: 30px;
            }
            .form-group {
                margin-bottom: 20px;
            }
            label {
                display: block;
                margin-bottom: 5px;
                color: #34495e;
                font-weight: bold;
            }
            input[type="text"], textarea {
                width: 100%;
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                box-sizing: border-box;
                font-size: 14px;
            }
            textarea {
                height: 100px;
                resize: vertical;
            }
            input[type="submit"] {
                background-color: #3498db;
                color: white;
                padding: 12px 20px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                width: 100%;
                font-size: 16px;
                transition: background-color 0.3s;
            }
            input[type="submit"]:hover {
                background-color: #2980b9;
            }
            .required {
                color: #e74c3c;
            }
            .helper-text {
                font-size: 12px;
                color: #7f8c8d;
                margin-top: 4px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Performance Marketing Blueprint Generator</h1>
            
            <form action="/generate_blueprint" method="post">
                <div class="form-group">
                    <label>Company Name <span class="required">*</span></label>
                    <input type="text" name="company_name" required placeholder="Enter your company name">
                </div>
                
                <div class="form-group">
                    <label>Product/Service <span class="required">*</span></label>
                    <input type="text" name="product_service" required placeholder="Describe your main product or service">
                </div>
                
                <div class="form-group">
                    <label>Target Audience <span class="required">*</span></label>
                    <input type="text" name="target_audience" required placeholder="Who is your ideal customer?">
                </div>
                
                <div class="form-group">
                    <label>Key Business Goal <span class="required">*</span></label>
                    <input type="text" name="business_goal" required placeholder="What is your primary business objective?">
                </div>
                
                <div class="form-group">
                    <label>Website</label>
                    <input type="text" name="website" placeholder="https://www.yourcompany.com">
                    <div class="helper-text">Optional: Include your website URL</div>
                </div>
                
                <div class="form-group">
                    <label>Current Marketing Efforts</label>
                    <textarea name="current_marketing" placeholder="Describe your current marketing activities..."></textarea>
                    <div class="helper-text">Optional: Tell us about your existing marketing strategies</div>
                </div>
                
                <input type="submit" value="Generate Blueprint PDF">
            </form>
        </div>
    </body>
    </html>
    """

# --- Main Execution ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(port)
# Use Render’s assigned PORT
    app.run(host="0.0.0.0", port=port)
