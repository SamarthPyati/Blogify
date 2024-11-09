from reportlab.lib.pagesizes import letter
from reportlab.platypus import Image, SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import seaborn as sns
import pandas as pd
from flask import send_file
import io

import matplotlib
matplotlib.use('Agg')  # Agg backend for non-GUI rendering
import matplotlib.pyplot as plt

def generate_pdf_report(data, engagement_data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"User Engagement Report for {data['username']}", styles['Heading1']))
    elements.append(Paragraph(f"Email: {data['email']}", styles['Normal']))
    elements.append(Paragraph(f"Total Posts: {data['total_posts']}", styles['Normal']))
    elements.append(Paragraph(f"Total Likes: {data['total_likes']}", styles['Normal']))
    elements.append(Paragraph(f"Total Dislikes: {data['total_dislikes']}", styles['Normal']))
    elements.append(Paragraph(f"Average Likes per Post: {data['average_likes']:.2f}", styles['Normal']))
    elements.append(Paragraph(f"Average Dislikes per Post: {data['average_dislikes']:.2f}", styles['Normal']))

    if data['most_liked_post']:
        elements.append(Paragraph(f"Most Liked Post: {data['most_liked_post'].title} ({data['most_liked_post'].likes_count} likes)", styles['Normal']))
    if data['most_disliked_post']:
        elements.append(Paragraph(f"Most Disliked Post: {data['most_disliked_post'].title} ({data['most_disliked_post'].dislikes_count} dislikes)", styles['Normal']))

    elements.append(Spacer(1, 12))

    for post in data['posts']:
        elements.append(Paragraph(f"Title: {post['title']}", styles['Normal']))
        elements.append(Paragraph(f"Date Posted: {post['date_posted'].strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        elements.append(Paragraph(f"Content: {post['content'][: 50]} ...", styles['Normal']))
        elements.append(Paragraph(f"Likes: {post['likes']}, Dislikes: {post['dislikes']}", styles['Normal']))
        elements.append(Spacer(1, 12))

    # Generate and add visualizations
    engagement_chart = generate_engagement_over_time_chart(engagement_data)
    reaction_pie_chart = generate_reaction_pie_chart(data)

    elements.append(Spacer(1, 12))
    elements.append(Paragraph("Engagement Over Time", styles['Heading2']))
    elements.append(Image(engagement_chart, width=400, height=300))

    elements.append(Spacer(1, 12))
    elements.append(Paragraph("Overall Reactions", styles['Heading2']))
    elements.append(Image(reaction_pie_chart, width=400, height=300))

    doc.build(elements)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"{data['username']}_report.pdf", mimetype='application/pdf')

    
def generate_csv_report(data):
    df = pd.DataFrame(data['posts'])
    buffer = io.BytesIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"{data['username']}_report.csv", mimetype='text/csv')

def generate_excel_report(data):
    df = pd.DataFrame(data['posts'])
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"{data['username']}_report.xlsx", mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

def generate_engagement_over_time_chart(engagement_data):
    df = pd.DataFrame(engagement_data)
    fig, ax = plt.subplots(figsize=(8, 6))

    sns.lineplot(x='dates', y='likes', data=df, ax=ax, label='Likes')
    sns.lineplot(x='dates', y='dislikes', data=df, ax=ax, label='Dislikes')

    ax.set_title('Engagement Over Time')
    ax.set_xlabel('Date')
    ax.set_ylabel('Count')
    ax.legend()

    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png')
    plt.close(fig)
    img_buffer.seek(0)
    return img_buffer

def generate_reaction_pie_chart(data):
    labels = ['Likes', 'Dislikes']
    sizes = [data['total_likes'], data['total_dislikes']]

    # Handle case where sizes are zero to avoid NaN error
    if sum(sizes) == 0:
        sizes = [1, 1]  # or any other appropriate fallback

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    ax.set_title('Overall Reactions')

    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png')
    plt.close(fig)  # Close the figure to release memory
    img_buffer.seek(0)

    return img_buffer