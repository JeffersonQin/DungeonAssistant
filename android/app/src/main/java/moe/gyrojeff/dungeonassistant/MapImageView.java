package moe.gyrojeff.dungeonassistant;


import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.util.AttributeSet;

public class MapImageView extends androidx.appcompat.widget.AppCompatImageView {
    private Paint redPaint;
    private float pointX, pointY;

    public MapImageView(Context context) {
        super(context);
        init();
    }

    public MapImageView(Context context, AttributeSet attrs) {
        super(context, attrs);
        init();
    }

    private void init() {
        // Initialize the red paint for drawing the point
        redPaint = new Paint();
        redPaint.setColor(Color.RED);
        redPaint.setStyle(Paint.Style.FILL);
    }

    public void updatePosition(float x, float y) {
        float viewWidth = this.getWidth();
        float viewHeight = this.getHeight();

        float imageWidth = this.getDrawable().getIntrinsicWidth();
        float imageHeight = this.getDrawable().getIntrinsicHeight();

        float new_x = 0;
        float new_y = 0;
        if (viewWidth / viewHeight < imageWidth / imageHeight) {
            new_x = x * imageWidth / imageWidth * viewWidth;
            float image_visualize_height = viewWidth / imageWidth * imageHeight;
            new_y = (viewHeight - image_visualize_height) / 2 + y * imageHeight / imageHeight * image_visualize_height;
        } else {
            float image_visualize_width = viewHeight / imageHeight * imageWidth;
            new_y = y * imageHeight / imageHeight * viewHeight;
            new_x = (viewWidth - image_visualize_width) / 2 + x * imageHeight / imageWidth * image_visualize_width;
        }

        // Update the position of the red point
        pointX = new_x;
        pointY = new_y;

        // Trigger a redraw
        invalidate();
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);

        // Draw the image on the canvas (assuming you have loaded the image)
        // Fill in your code here to draw the image

        // Draw the red point on top of the image
        canvas.drawCircle(pointX, pointY, 10, redPaint);
    }
}