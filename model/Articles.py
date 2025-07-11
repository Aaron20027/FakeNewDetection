
class Articles():
    def __init__(self,article_id,
title,
article_text,
label,
sentiment,
sentiment_intensity,
sources,
submitted_by,
submitted_at,
factchecked_by,
factchecked_at,
status,
updated_at,):
        self.article_id = article_id
        self.title = title
        self.article_text = article_text
        self.label = label
        self.sentiment = sentiment
        self.sentiment_intensity = sentiment_intensity
        self.sources = sources
        self.submitted_by = submitted_by
        self.submitted_at = submitted_at
        self.factchecked_by = factchecked_by
        self.factchecked_at = factchecked_at
        self.status = status
        self.updated_at = updated_at
        
  