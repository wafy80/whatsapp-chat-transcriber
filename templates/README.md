# HTML Templates

This folder contains HTML templates for PDF generation.

## Available Templates

### template.html (Default)
Full WhatsApp-style layout with:
- Green message bubbles for user messages
- White bubbles for other participants
- Message statistics (total messages, media, transcriptions)
- Date dividers
- Audio transcription display
- Image embedding support

### template_minimal.html
Clean, minimal layout with:
- Simple text-based design
- No bubble styling
- Compact message display
- Essential information only

### template_simple.html
Simple text layout with:
- Basic formatting
- Clear message structure
- No visual embellishments
- Good for printing

## Creating Custom Templates

You can create your own templates by copying an existing one:

```bash
cp templates/template.html templates/my_template.html
```

Then edit `config.ini`:
```ini
[HTML_TEMPLATE]
enabled = true
template_file = templates/my_template.html
```

## Template Syntax

### Variables

**Global Variables:**
- `{{chat_title}}` - Name of the chat
- `{{generation_date}}` - When the PDF was generated
- `{{total_messages}}` - Total number of messages
- `{{total_media}}` - Total media files
- `{{total_transcriptions}}` - Total transcribed audio files

**Message Variables (inside `{{#each messages}}`)**
- `{{this.sender}}` - Message sender name
- `{{this.date}}` - Message date
- `{{this.time}}` - Message time
- `{{this.text}}` - Message text content
- `{{this.transcription}}` - Audio transcription (if available)
- `{{this.message_class}}` - CSS class: "user" or "other"
- `{{this.current_date}}` - Current date for date dividers
- `{{this.is_system}}` - True if system message

### Conditionals

```html
{{#if condition}}
  Content shown if true
{{/if}}

{{#if condition}}
  Content if true
{{else}}
  Content if false
{{/if}}

{{#unless condition}}
  Content shown if false
{{/unless}}
```

### Loops

```html
{{#each messages}}
  <div>{{this.sender}}: {{this.text}}</div>
{{/each}}
```

### Example: Custom Message Block

```html
{{#each messages}}
  {{#if this.is_system}}
    <!-- System message -->
    <div class="system-message">
      {{this.text}}
    </div>
  {{else}}
    <!-- Regular message -->
    <div class="message {{this.message_class}}">
      <strong>{{this.sender}}</strong>
      <span class="time">{{this.time}}</span>
      <p>{{this.text}}</p>
      
      {{#if this.transcription}}
        <div class="transcription">
          🎙️ {{this.transcription}}
        </div>
      {{/if}}
      
      {{#if this.media}}
        {{#if this.media.is_image}}
          <img src="{{this.media.path}}" alt="{{this.media.filename}}">
        {{else}}
          <p>📎 {{this.media.filename}}</p>
        {{/if}}
      {{/if}}
    </div>
  {{/if}}
{{/each}}
```

## Styling

Templates support full CSS. Add your styles in the `<style>` section:

```html
<style>
  .message.user {
    background-color: #DCF8C6;
    margin-left: 20%;
  }
  
  .message.other {
    background-color: #FFFFFF;
    margin-right: 20%;
  }
  
  .transcription {
    font-style: italic;
    color: #666;
  }
</style>
```

## Tips

1. **Keep it simple** - Complex layouts may not render well in PDF
2. **Test thoroughly** - Generate test PDFs with different chat types
3. **Use web fonts carefully** - Not all fonts work in PDF generation
4. **Optimize images** - Large images can make PDFs very big
5. **Consider printing** - Some designs work better on screen than paper

## Troubleshooting

**Template not found:**
- Check that the file exists in `templates/` folder
- Verify the path in `config.ini` includes `templates/` prefix
- Use forward slashes even on Windows: `templates/my_template.html`

**Template doesn't render:**
- Check for syntax errors in `{{variables}}`
- Validate HTML (closing tags, proper nesting)
- Look at console output for error messages

**Styling issues:**
- WeasyPrint doesn't support all CSS features
- Avoid `position: fixed` and advanced CSS
- Use tables for complex layouts
- Test with different PDF viewers

## Resources

- [WeasyPrint Documentation](https://weasyprint.org/)
- [Jinja2 Template Syntax](https://jinja.palletsprojects.com/) (similar syntax)
- CSS for print: [Print Stylesheets Guide](https://www.smashingmagazine.com/2018/05/print-stylesheets-in-2018/)

---

For more information, see the main README.md
