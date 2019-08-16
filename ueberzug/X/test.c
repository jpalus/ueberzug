#include <stdio.h>
#include <X11/Xlib.h>

#define ARRAY_LENGTH(stack_array) \
    (sizeof stack_array \
     ? sizeof stack_array / sizeof *stack_array \
     : 0)

int main() {
    static int array0[] = {};
    static int array1[] = {1, 2, 3};
    static int array2[] = {1, 3};
    int array3[] = {1,};
    static XRectangle rects[4];
	rects[3].x = 5;
	rects[3].y = 7;
	rects[3].width = 8;
	rects[3].height = 9;
    printf("size:%d\n", ARRAY_LENGTH(array0));
    printf("size:%d\n", ARRAY_LENGTH(array1));
    printf("size:%d\n", ARRAY_LENGTH(array2));
    printf("size:%d\n", ARRAY_LENGTH(array3));
    printf("rects size:%d\n", ARRAY_LENGTH(rects));
    printf("last rect:%d %d, %dx%d", rects[3].x, rects[3].y, rects[3].width, rects[3].height);
}
